from django.db import models
from django.contrib.auth.models import User
import uuid

class Organization(models.Model):
    name = models.CharField(max_length=255)
    invite_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organizations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class OrganizationMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organization')

    def __str__(self):
        return f"{self.user.username} in {self.organization.name}"

class Cluster(models.Model):
    name = models.CharField(max_length=255)
    total_ram = models.IntegerField(help_text="Total RAM in GB")  # in GB
    total_cpu = models.IntegerField(help_text="Total CPU cores")  # in cores
    total_gpu = models.IntegerField(help_text="Total GPU units")  # in units
    allocated_ram = models.IntegerField(default=0)
    allocated_cpu = models.IntegerField(default=0)
    allocated_gpu = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clusters')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def available_ram(self):
        return self.total_ram - self.allocated_ram

    @property
    def available_cpu(self):
        return self.total_cpu - self.allocated_cpu

    @property
    def available_gpu(self):
        return self.total_gpu - self.allocated_gpu


class Deployment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        COMPLETED = 'COMPLETED', 'Completed'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'

    docker_image_path = models.URLField()
    required_ram = models.IntegerField()
    required_cpu = models.IntegerField()
    required_gpu = models.IntegerField()
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='dependent_deployments',
        blank=True
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)
    cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, related_name='deployments')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def release_resources(self):
        """Release allocated resources back to the cluster"""
        self.cluster.allocated_ram -= self.required_ram
        self.cluster.allocated_cpu -= self.required_cpu
        self.cluster.allocated_gpu -= self.required_gpu
        self.cluster.save()
        self.status = self.Status.PENDING
        self.save()
    def __str__(self):
        return f"{self.docker_image_path} ({self.status})"

class Role(models.Model):
    class RoleType(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DEVELOPER = 'DEVELOPER', 'Developer'
        VIEWER = 'VIEWER', 'Viewer'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=RoleType.choices)

    class Meta:
        unique_together = ('user', 'organization')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
