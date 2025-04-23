# insurance/serializers.py

from rest_framework import serializers
from .models import InsuranceProfile, InsurancePlan, InsuranceClaim, InsurancePayment


class InsurancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePlan
        fields = '__all__'


class InsuranceProfileSerializer(serializers.ModelSerializer):
    active_plan = InsurancePlanSerializer()

    class Meta:
        model = InsuranceProfile
        fields = '__all__'


class InsuranceClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceClaim
        fields = '__all__'


class InsurancePaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsurancePayment
        fields = '__all__'
