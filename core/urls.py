from django.urls import path
from .views import RegisterView, LoginView, ProfileView
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
]
