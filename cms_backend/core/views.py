from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from .serializers import LoginSerializer, UserSerializer
from core.utils.response_helpers import success_response, error_response
from rest_framework.response import Response

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid username or password",
                data=serializer.errors,
                http_status=status.HTTP_400_BAD_REQUEST
            )

        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)

        return success_response(
            data={
                "token": token.key,
                "user": UserSerializer(user).data
            },
            message="Login successful",
            http_status=status.HTTP_200_OK
        )


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)

        return Response({
            "success": True,
            "message":"Logout successful"
        },status=status.HTTP_200_OK)
