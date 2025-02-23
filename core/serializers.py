from rest_framework import serializers
from django.contrib.auth.models import User, Group
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Organization, OrganizationMember, Cluster, Deployment, Role


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(
        choices=Role.RoleType.choices,
        write_only=True
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'role')

    def create(self, validated_data):
        role = validated_data.pop('role').title()
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        group = Group.objects.get(name=role)
        user.groups.add(group)
        user = User.objects.get(pk=user.pk)
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['role'] = instance.groups.first().name  # Include role in response
        return representation

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

class OrganizationSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    invite_code = serializers.UUIDField(read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'name', 'invite_code', 'created_by', 'created_at')

class JoinOrganizationSerializer(serializers.Serializer):
    invite_code = serializers.CharField()

    def validate_invite_code(self, value):
        try:
            return Organization.objects.get(invite_code=value)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Invalid invite code.")

class ClusterSerializer(serializers.ModelSerializer):
    available_ram = serializers.IntegerField(read_only=True)
    available_cpu = serializers.IntegerField(read_only=True)
    available_gpu = serializers.IntegerField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Cluster
        fields = [
            'id', 'name',
            'total_ram', 'total_cpu', 'total_gpu',
            'allocated_ram', 'allocated_cpu', 'allocated_gpu',
            'available_ram', 'available_cpu', 'available_gpu',
            'created_by', 'created_at'
        ]
        read_only_fields = [
            'allocated_ram', 'allocated_cpu', 'allocated_gpu',
            'created_by', 'created_at'
        ]

class DeploymentSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    cluster = serializers.PrimaryKeyRelatedField(queryset=Cluster.objects.all())

    class Meta:
        model = Deployment
        fields = [
            'id', 'docker_image_path', 'status', 'priority',
            'required_ram', 'required_cpu', 'required_gpu',
            'cluster', 'created_by', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        if data['required_ram'] <= 0 or data['required_cpu'] <= 0 or data['required_gpu'] < 0:
            raise serializers.ValidationError("Resource values must be positive")
        return data