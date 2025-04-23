# insurance/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import InsuranceProfile, InsurancePlan, InsuranceClaim
from .serializers import InsuranceProfileSerializer, InsurancePlanSerializer, InsuranceClaimSerializer


class InsurancePlanListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        plans = InsurancePlan.objects.all()
        serializer = InsurancePlanSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class InsuranceProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.profile.insurance_profile
            serializer = InsuranceProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except InsuranceProfile.DoesNotExist:
            return Response({'error': 'Insurance profile not found.'}, status=status.HTTP_404_NOT_FOUND)


class InsuranceClaimView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = InsuranceClaimSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
