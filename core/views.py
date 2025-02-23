from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Organization, OrganizationMember, Cluster
from .serializers import OrganizationSerializer, JoinOrganizationSerializer, ClusterSerializer
from .swagger import JWTSwaggerAutoSchema
from django_rq import job, get_queue
from .models import Deployment
from .serializers import DeploymentSerializer
from django.db import models
from django.db import transaction
from .permissions import IsAdmin, IsDeveloper, IsViewer, IsAdminOrReadOnly


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    schema_class = JWTSwaggerAutoSchema

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    schema_class = JWTSwaggerAutoSchema
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            token = response.data['access']
            refresh_token = response.data['refresh']
            return Response({
                'access_token': token,
                'refresh_token': refresh_token,
            })
        return response

class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    schema_class = JWTSwaggerAutoSchema
    def get_object(self):
        return self.request.user

class CreateOrganizationView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSerializer
    schema_class = JWTSwaggerAutoSchema

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class GenerateInviteCodeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrganizationSerializer
    schema_class = JWTSwaggerAutoSchema
    queryset = Organization.objects.all()

    def get_object(self):
        organization = super().get_object()
        if organization.created_by != self.request.user:
            self.permission_denied(self.request, "You are not the creator of this organization.")
        return organization

class JoinOrganizationView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JoinOrganizationSerializer
    schema_class = JWTSwaggerAutoSchema

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.validated_data['invite_code']

        if OrganizationMember.objects.filter(user=request.user, organization=organization).exists():
            return Response(
                {"detail": "You are already a member of this organization."},
                status=status.HTTP_400_BAD_REQUEST
            )

        OrganizationMember.objects.create(user=request.user, organization=organization)
        return Response(
            {"detail": "Successfully joined the organization."},
            status=status.HTTP_201_CREATED
        )

class ClusterListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = ClusterSerializer
    schema_class = JWTSwaggerAutoSchema

    def get_queryset(self):
        return Cluster.objects.select_related('created_by').prefetch_related('deployments')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ClusterDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClusterSerializer
    schema_class = JWTSwaggerAutoSchema
    queryset = Cluster.objects.all()

@job('default', timeout=3600)
def process_deployment(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)

    cluster = deployment.cluster
    if (cluster.available_ram >= deployment.required_ram and
            cluster.available_cpu >= deployment.required_cpu and
            cluster.available_gpu >= deployment.required_gpu):

        cluster.allocated_ram += deployment.required_ram
        cluster.allocated_cpu += deployment.required_cpu
        cluster.allocated_gpu += deployment.required_gpu
        cluster.save()

        deployment.status = Deployment.Status.RUNNING
        deployment.save()
    else:
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        get_queue('default').enqueue(process_deployment, deployment.id)


class DeploymentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsDeveloper]
    serializer_class = DeploymentSerializer
    schema_class = JWTSwaggerAutoSchema

    def get_queryset(self):
        return Deployment.objects.select_related('cluster', 'created_by')\
                   .prefetch_related('dependencies')
    def perform_create(self, serializer):
        deployment = serializer.save(created_by=self.request.user)
        process_deployment.delay(deployment.id)


class DeploymentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeploymentSerializer
    schema_class = JWTSwaggerAutoSchema
    queryset = Deployment.objects.all()


def find_preemptable_deployments(cluster, current_priority):
    PRIORITY_ORDER = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    return Deployment.objects.filter(
        cluster=cluster,
        status=Deployment.Status.RUNNING,
    ).annotate(
        priority_order=models.Case(
            *[models.When(priority=p, then=v) for p, v in PRIORITY_ORDER.items()],
            output_field=models.IntegerField()
        )
    ).filter(priority_order__lt=PRIORITY_ORDER[current_priority]).order_by('priority_order')


@job('default', timeout=3600)
def process_deployment(deployment_id):
    deployment = Deployment.objects.get(id=deployment_id)
    cluster = deployment.cluster

    print(f"Processing deployment {deployment.id} (priority: {deployment.priority})")
    print(f"Cluster resources - Total: {cluster.total_ram}GB, Allocated: {cluster.allocated_ram}GB, Available: {cluster.available_ram}GB")

    def can_allocate(deployment):
        return (
            cluster.available_ram >= deployment.required_ram and
            cluster.available_cpu >= deployment.required_cpu and
            cluster.available_gpu >= deployment.required_gpu
        )

    def dependencies_completed(deployment):
        return all(dep.status == Deployment.Status.COMPLETED for dep in deployment.dependencies.all())

    with transaction.atomic():
        if not dependencies_completed(deployment):
            print("Dependencies not completed, re-queuing deployment")
            deployment.status = Deployment.Status.PENDING
            deployment.save()
            get_queue('default').enqueue(process_deployment, deployment.id)
            return
        if can_allocate(deployment):
            print("Direct allocation possible")
            cluster.allocated_ram += deployment.required_ram
            cluster.allocated_cpu += deployment.required_cpu
            cluster.allocated_gpu += deployment.required_gpu
            cluster.save()
            deployment.status = Deployment.Status.RUNNING
            deployment.save()
            return

        preemptable = find_preemptable_deployments(cluster, deployment.priority)
        print(f"Found {preemptable.count()} preemptable deployments")

        preempted_deployments = []

        for victim in preemptable:
            print(f"Preempting deployment {victim.id} (priority: {victim.priority})")
            victim.release_resources()
            preempted_deployments.append(victim)
            print('Cluster after victim release ', cluster)

            if can_allocate(deployment):
                print("Allocation possible after preemption")
                cluster.allocated_ram += deployment.required_ram
                cluster.allocated_cpu += deployment.required_cpu
                cluster.allocated_gpu += deployment.required_gpu
                cluster.save()
                deployment.status = Deployment.Status.RUNNING
                deployment.save()

                for preempted in preempted_deployments:
                    get_queue('default').enqueue(process_deployment, preempted.id)
                return

        print("Insufficient resources, re-queuing deployment")
        deployment.status = Deployment.Status.PENDING
        deployment.save()
        get_queue('default').enqueue(process_deployment, deployment.id)


