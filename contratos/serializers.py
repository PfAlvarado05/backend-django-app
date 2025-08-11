from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Contrato, Trabajador, Semana, RegistroDiario, DiaNoLaborable, Gasto

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ContratoSerializer(serializers.ModelSerializer):
    ganancia_neta = serializers.FloatField(read_only=True)

    class Meta:
        model = Contrato
        fields = '__all__'
        read_only_fields = ['usuario', 'ganancia_neta']

class TrabajadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trabajador
        fields = ['id', 'nombre', 'oficio']

class SemanaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semana
        fields = '__all__'
class RegistroDiarioSerializer(serializers.ModelSerializer):
    pago_total = serializers.SerializerMethodField()

    class Meta:
        model = RegistroDiario
        fields = '__all__' 

    def get_pago_total(self, obj):
        return obj.pago_total()
class DiaNoLaborableSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiaNoLaborable
        fields = '__all__'

class GastoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gasto
        fields = ['id', 'nombre', 'costo', 'semana']
