from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, CustomTokenObtainPairSerializer
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