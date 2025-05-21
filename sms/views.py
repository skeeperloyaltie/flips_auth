from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from .models import SMSConfig, SMSLog, LoginCode
from .serializers import SMSConfigSerializer, SMSLogSerializer, LoginCodeSerializer
from .utils import send_login_code

class SMSConfigView(generics.ListCreateAPIView):
    queryset = SMSConfig.objects.all()
    serializer_class = SMSConfigSerializer
    permission_classes = [IsAdminUser]

class SMSLogView(generics.ListAPIView):
    queryset = SMSLog.objects.all()
    serializer_class = SMSLogSerializer
    permission_classes = [IsAdminUser]

class LoginCodeView(generics.CreateAPIView):
    serializer_class = LoginCodeSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new login code
        login_code = LoginCode(phone_number=phone_number)
        login_code.save()

        # Send the login code via SMS
        sms_sent = send_login_code(phone_number, login_code.code)
        if not sms_sent:
            return Response({"error": "Failed to send login code"}, status=status.HTTP_500_INTERNAL_server_ERROR)

        serializer = self.get_serializer(login_code)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class VerifyLoginCodeView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')

        if not phone_number or not code:
            return Response({"error": "Phone number and code are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            login_code = LoginCode.objects.get(phone_number=phone_number, code=code)
            if not login_code.is_valid():
                return Response({"error": "Invalid or expired code"}, status=status.HTTP_400_BAD_REQUEST)

            login_code.is_used = True
            login_code.save()
            return Response({"message": "Login code verified successfully"}, status=status.HTTP_200_OK)

        except LoginCode.DoesNotExist:
            return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)