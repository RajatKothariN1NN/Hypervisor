from django.urls import path
from .views import RegisterView, LoginView, ProfileView, ClusterListCreateView, ClusterDetailView, \
    DeploymentListCreateView, DeploymentDetailView
from django.urls import path
from .views import (
    CreateOrganizationView,
    GenerateInviteCodeView,
    JoinOrganizationView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),

    path('organizations/', CreateOrganizationView.as_view(), name='create-organization'),
    path('organizations/<int:pk>/invite-code/', GenerateInviteCodeView.as_view(), name='get-invite-code'),
    path('organizations/join/', JoinOrganizationView.as_view(), name='join-organization'),

    path('clusters/', ClusterListCreateView.as_view(), name='cluster-list-create'),
    path('clusters/<int:pk>/', ClusterDetailView.as_view(), name='cluster-detail'),

    path('deployments/', DeploymentListCreateView.as_view(), name='deployment-list-create'),
    path('deployments/<int:pk>/', DeploymentDetailView.as_view(), name='deployment-detail'),

]
