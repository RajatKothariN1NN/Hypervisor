from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer, JoinOrganizationSerializer
from .swagger import JWTSwaggerAutoSchema


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