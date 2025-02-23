from django.urls import reverse
from django_rq import get_worker
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from .models import Organization, OrganizationMember, Cluster, Deployment
from .views import process_deployment


class AuthTests(APITestCase):
    def setUp(self):
        # Create groups if they don't exist
        Group.objects.get_or_create(name='ADMIN')
        Group.objects.get_or_create(name='DEVELOPER')
        Group.objects.get_or_create(name='VIEWER')

    def test_register_user(self):
        url = reverse('register')
        data = {
            'username': 'testuser1',
            'password': 'testpass123',
            'role': 'VIEWER'
        }
        response = self.client.post(url, data, format='json')
        print(response.data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='testuser1').exists())

    def test_login_user(self):
        User.objects.create_user(username='testuser1', password='testpass123')
        url = reverse('login')
        data = {'username': 'testuser1', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in response.data)
        self.assertTrue('refresh_token' in response.data)

    def test_profile_access(self):
        user = User.objects.create_user(username='testuser1', password='testpass123', role='Admin')
        self.client.force_authenticate(user=user)
        url = reverse('profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser1')
class OrganizationTests(APITestCase):
    def setUp(self):
        Group.objects.get_or_create(name='Admin')
        self.user = User.objects.create_user(username="admin", password="admin123")
        admin_group = Group.objects.get(name='Admin')
        self.user.groups.add(admin_group)
        self.client.force_authenticate(user=self.user)
        self.org = Organization.objects.create(name="Test Org", created_by=self.user)

    def test_create_organization(self):
        url = reverse('create-organization')
        data = {"name": "New Org"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Organization.objects.count(), 2)

    def test_get_invite_code(self):
        url = reverse('get-invite-code', args=[self.org.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['invite_code'], str(self.org.invite_code))

    def test_join_organization(self):
        url = reverse('join-organization')
        data = {"invite_code": str(self.org.invite_code)}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(OrganizationMember.objects.filter(
            user=self.user,
            organization=self.org
        ).exists())

class ClusterTests(APITestCase):
    def setUp(self):
        Group.objects.get_or_create(name='Admin')
        self.user = User.objects.create_user(username="admin", password="admin123")
        admin_group = Group.objects.get(name='Admin')
        self.user.groups.add(admin_group)
        self.client.force_authenticate(user=self.user)

    def test_create_cluster(self):
        url = reverse('cluster-list-create')
        data = {
            "name": "Test Cluster",
            "total_ram": 64,
            "total_cpu": 16,
            "total_gpu": 4
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Cluster.objects.count(), 1)
        self.assertEqual(Cluster.objects.first().created_by, self.user)

    def test_list_clusters(self):
        Cluster.objects.create(
            name="Test Cluster",
            total_ram=64,
            total_cpu=16,
            total_gpu=4,
            created_by=self.user
        )
        url = reverse('cluster-list-create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_cluster_detail(self):
        cluster = Cluster.objects.create(
            name="Test Cluster",
            total_ram=64,
            total_cpu=16,
            total_gpu=4,
            created_by=self.user
        )
        url = reverse('cluster-detail', args=[cluster.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], "Test Cluster")

class DeploymentTests(APITestCase):
    def setUp(self):
        Group.objects.get_or_create(name='DEVELOPER')

        # Create developer user
        self.user = User.objects.create_user(username="dev", password="dev123")
        dev_group = Group.objects.get(name='Developer')
        print(dev_group)
        self.user.groups.add(dev_group)
        self.user.save()
        print('Hi, the user is : ', self.user, self.user.groups)
        self.cluster = Cluster.objects.create(
            name="Test Cluster",
            total_ram=64,
            total_cpu=16,
            total_gpu=4,
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_deployment(self):
        url = reverse('deployment-list-create')
        data = {
            "docker_image_path": "https://0.0.0.0/ml-model:v1",
            "required_ram": 16,
            "required_cpu": 4,
            "required_gpu": 1,
            "priority": "HIGH",
            "cluster": self.cluster.id,
            'created_by': self.user.id
        }
        print('Hi, the user role is : ', self.user.groups)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Deployment.objects.count(), 1)
        self.assertEqual(Deployment.objects.first().status, 'PENDING')

# class SchedulingTests(APITestCase):
#     def setUp(self):
#         self.user = User.objects.create_user(username="admin", password="admin123")
#         self.cluster = Cluster.objects.create(
#             name="Test Cluster",
#             total_ram=64,
#             total_cpu=16,
#             total_gpu=4,
#             created_by=self.user
#         )
#         self.client.force_authenticate(user=self.user)
#
#     def test_preemption_logic(self):
#         # Create low-priority deployment
#         low_deploy = Deployment.objects.create(
#             docker_image_path="https://localhost/low-priority-image",
#             required_ram=32,
#             required_cpu=8,
#             required_gpu=2,
#             priority="LOW",
#             cluster=self.cluster,
#             created_by=self.user,
#             status=Deployment.Status.RUNNING
#         )
#         self.cluster.allocated_ram = 32
#         self.cluster.allocated_cpu = 8
#         self.cluster.allocated_gpu = 2
#         self.cluster.save()
#
#         # Create high-priority deployment
#         high_deploy = Deployment.objects.create(
#             docker_image_path="https://localhost/high-priority-image",
#             required_ram=48,
#             required_cpu=12,
#             required_gpu=3,
#             priority="HIGH",
#             cluster=self.cluster,
#             created_by=self.user
#         )
#
#         # # Process deployment (should preempt low-priority)
#         # process_deployment(high_deploy.id)
#         #
#         # # Verify preemption
#         # low_deploy.refresh_from_db()
#         # high_deploy.refresh_from_db()
#         # self.assertEqual(low_deploy.status, Deployment.Status.PENDING)
#         # self.assertEqual(high_deploy.status, Deployment.Status.RUNNING)
#         # self.assertEqual(self.cluster.allocated_ram, 48)
#         process_deployment(high_deploy.id)
#         get_worker().work(burst=True)  # Process all enqueued jobs
#
#         # Verify preemption
#         low_deploy.refresh_from_db()
#         high_deploy.refresh_from_db()
#         self.assertEqual(low_deploy.status, Deployment.Status.PENDING)
#         self.assertEqual(high_deploy.status, Deployment.Status.RUNNING)
#         self.assertEqual(self.cluster.allocated_ram, 48)

class SchedulingTests(APITestCase):
    def setUp(self):
        Group.objects.get_or_create(name='Admin')
        self.user = User.objects.create_user(username="admin", password="admin123")
        admin_group = Group.objects.get(name='Admin')
        self.user.groups.add(admin_group)
        self.cluster = Cluster.objects.create(
            name="Test Cluster",
            total_ram=64,
            total_cpu=16,
            total_gpu=4,
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_preemption_logic(self):
        # Create low-priority deployment
        low_deploy = Deployment.objects.create(
            docker_image_path="https://localhost/low-priority-image",
            required_ram=32,
            required_cpu=8,
            required_gpu=2,
            priority="LOW",
            cluster=self.cluster,
            created_by=self.user,
            status=Deployment.Status.RUNNING
        )
        self.cluster.allocated_ram = 32
        self.cluster.allocated_cpu = 8
        self.cluster.allocated_gpu = 2
        self.cluster.save()

        # Create high-priority deployment
        high_deploy = Deployment.objects.create(
            docker_image_path="https://localhost/high-priority-image",
            required_ram=48,
            required_cpu=12,
            required_gpu=3,
            priority="HIGH",
            cluster=self.cluster,
            created_by=self.user
        )

        # Process deployment (should preempt low-priority)
        process_deployment(high_deploy.id)
        get_worker().work(burst=True)  # Execute all jobs immediately

        # Verify preemption
        low_deploy.refresh_from_db()
        high_deploy.refresh_from_db()
        self.cluster.refresh_from_db()

        # Check low-priority deployment is preempted
        self.assertEqual(low_deploy.status, Deployment.Status.PENDING)
        # Check high-priority deployment is running
        self.assertEqual(high_deploy.status, Deployment.Status.RUNNING)
        # Check cluster resources are updated
        self.assertEqual(self.cluster.allocated_ram, 48)
        self.assertEqual(self.cluster.allocated_cpu, 12)
        self.assertEqual(self.cluster.allocated_gpu, 3)

class RBACTests(APITestCase):
    def setUp(self):
        # Create groups
        Group.objects.get_or_create(name='Admin')
        Group.objects.get_or_create(name='Developer')
        Group.objects.get_or_create(name='Viewer')

        # Create test users
        self.admin = User.objects.create_user(username="admin", password="admin123")
        admin_group = Group.objects.get(name='Admin')
        self.admin.groups.add(admin_group)

        self.developer = User.objects.create_user(username="dev", password="dev123")
        dev_group = Group.objects.get(name='Developer')
        self.developer.groups.add(dev_group)

    def test_admin_cluster_creation(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('cluster-list-create')
        data = {"name": "Test Cluster", "total_ram": 64, "total_cpu": 16, "total_gpu": 4}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)

    def test_developer_cluster_creation(self):
        self.client.force_authenticate(user=self.developer)
        url = reverse('cluster-list-create')
        data = {"name": "Test Cluster", "total_ram": 64, "total_cpu": 16, "total_gpu": 4}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)

class DeploymentDependencyTests(APITestCase):
    def setUp(self):
        Group.objects.get_or_create(name='DEVELOPER')

        # Create developer user
        self.user = User.objects.create_user(username="dev", password="dev123")
        dev_group = Group.objects.get(name='Developer')
        print(dev_group)
        self.user.groups.add(dev_group)
        self.user.save()
        print('Hi, the user is : ', self.user, self.user.groups)
        self.cluster = Cluster.objects.create(
            name="Test Cluster",
            total_ram=64,
            total_cpu=16,
            total_gpu=4,
            created_by=self.user
        )
        self.client.force_authenticate(user=self.user)


    def test_dependency_handling(self):
        # Create dependency deployment
        dependency = Deployment.objects.create(
            docker_image_path="dependency-image",
            required_ram=16,
            required_cpu=4,
            required_gpu=1,
            priority="LOW",
            cluster=self.cluster,
            created_by=self.user
        )

        # Create dependent deployment
        dependent = Deployment.objects.create(
            docker_image_path="dependent-image",
            required_ram=16,
            required_cpu=4,
            required_gpu=1,
            priority="HIGH",
            cluster=self.cluster,
            created_by=self.user
        )
        dependent.dependencies.add(dependency)

        # Process dependent deployment
        process_deployment(dependent.id)
        get_worker().work(burst=True)

        # Verify dependency handling
        dependent.refresh_from_db()
        self.assertEqual(dependent.status, Deployment.Status.PENDING)

        # Mark dependency as completed
        dependency.status = Deployment.Status.COMPLETED
        dependency.save()

        # Process dependent deployment again
        process_deployment(dependent.id)
        get_worker().work(burst=True)

        # Verify dependent deployment is running
        dependent.refresh_from_db()
        self.assertEqual(dependent.status, Deployment.Status.RUNNING)