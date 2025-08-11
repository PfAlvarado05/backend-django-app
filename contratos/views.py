from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.http import FileResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from datetime import timedelta
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import os
from .utils import generar_reporte_pdf_semanal
from .models import Contrato, Trabajador, Gasto, Semana, RegistroDiario, DiaNoLaborable
from .serializers import (
    RegisterSerializer, ContratoSerializer, TrabajadorSerializer,
    GastoSerializer, SemanaSerializer, RegistroDiarioSerializer, DiaNoLaborableSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
        except Exception as e:
            if 'unique' in str(e).lower():
                return Response(
                    {'error': 'El nombre de usuario ya existe. Por favor elige otro.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    
#class LoginView(APIView):
 #   permission_classes = [permissions.AllowAny]
#  def post(self, request):
    #    user = authenticate(username=request.data.get('username'), password=request.data.get('password'))
     #   if user:
 #           token, _ = Token.objects.get_or_create(user=user)
  #          return Response({'token': token.key})
   #     return Response({'error': 'Credenciales inválidas'}, status=401)

class ContratoListCreateView(generics.ListCreateAPIView):
    serializer_class = ContratoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contrato.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        contrato = serializer.save(usuario=self.request.user)
        semanas = contrato.duracion_semanas()
        for i in range(semanas):
            inicio = contrato.fecha_inicio + timedelta(weeks=i)
            fin = min(inicio + timedelta(days=6), contrato.fecha_fin)
            Semana.objects.create(contrato=contrato, numero_semana=i+1, fecha_inicio=inicio, fecha_fin=fin)

class TrabajadorListCreateView(generics.ListCreateAPIView):
    serializer_class = TrabajadorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Trabajador.objects.filter(contrato__id=self.kwargs['contrato_id'], contrato__usuario=self.request.user)

    def perform_create(self, serializer):
        contrato = get_object_or_404(Contrato, pk=self.kwargs['contrato_id'], usuario=self.request.user)
        serializer.save(contrato=contrato)


class GastoListCreateView(generics.ListCreateAPIView):
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Gasto.objects.filter(contrato__id=self.kwargs['contrato_id'], contrato__usuario=self.request.user)

    def perform_create(self, serializer):
        contrato = get_object_or_404(Contrato, pk=self.kwargs['contrato_id'], usuario=self.request.user)
        serializer.save(contrato=contrato)

        
class GastoPorSemanaListCreateView(generics.ListCreateAPIView):
    serializer_class = GastoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Gasto.objects.filter(semana__id=self.kwargs['semana_id'], contrato__usuario=self.request.user)

    def perform_create(self, serializer):
        semana = get_object_or_404(Semana, pk=self.kwargs['semana_id'], contrato__usuario=self.request.user)
        serializer.save(contrato=semana.contrato, semana=semana)

class SemanaListView(generics.ListAPIView):
    serializer_class = SemanaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Semana.objects.filter(contrato__id=self.kwargs['contrato_id'], contrato__usuario=self.request.user)

class RegistroDiarioListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, contrato_id):
        semana_id = request.GET.get('semana_id')  # Cambiado de 'semana' a 'semana_id'
        if not semana_id:
            return Response({'error': 'Parámetro semana_id requerido'}, status=400)
        
        contrato = get_object_or_404(Contrato, id=contrato_id, usuario=request.user)
        
        try:
            semana = Semana.objects.get(
                contrato=contrato,
                id=semana_id  # Usar ID de la semana
            )
        except Semana.DoesNotExist:
            return Response({'error': 'Semana no encontrada para este contrato'}, status=404)

        registros = RegistroDiario.objects.filter(
            semana=semana,
            trabajador__contrato=contrato
        )
        serializer = RegistroDiarioSerializer(registros, many=True)
        return Response(serializer.data)

    def post(self, request, contrato_id):
        contrato = get_object_or_404(Contrato, id=contrato_id, usuario=request.user)
        serializer = RegistroDiarioSerializer(data=request.data)
        
        if serializer.is_valid():
            semana = serializer.validated_data.get('semana')
            if semana.contrato != contrato:
                return Response({'error': 'La semana no pertenece al contrato'}, status=400)
            
            trabajador = serializer.validated_data.get('trabajador')
            if trabajador.contrato != contrato:
                return Response({'error': 'El trabajador no pertenece al contrato'}, status=400)
            
            dia = serializer.validated_data.get('dia')
            registro, created = RegistroDiario.objects.get_or_create(
                semana=semana,
                trabajador=trabajador,
                dia=dia,
                defaults=serializer.validated_data
            )
            
            if not created:
                registro.unidades = serializer.validated_data.get('unidades')
                registro.save()
                
            return Response(RegistroDiarioSerializer(registro).data, status=200 if not created else 201)
            
        return Response(serializer.errors, status=400)


class DiaNoLaborableListCreateView(generics.ListCreateAPIView):
    serializer_class = DiaNoLaborableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiaNoLaborable.objects.filter(contrato__id=self.kwargs['contrato_id'], contrato__usuario=self.request.user)

    def perform_create(self, serializer):
        contrato = get_object_or_404(Contrato, pk=self.kwargs['contrato_id'], usuario=self.request.user)
        serializer.save(contrato=contrato)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generar_pdf_reporte_semana(request, contrato_id):
    semana_numero = int(request.GET.get("semana", 1))
    contrato = get_object_or_404(Contrato, id=contrato_id, usuario=request.user)
    path_pdf = generar_reporte_pdf_semanal(contrato, semana_numero)

    relative_path = os.path.relpath(path_pdf, settings.MEDIA_ROOT)
    url_pdf = request.build_absolute_uri(settings.MEDIA_URL + relative_path)

    return Response({'url_reporte': url_pdf})
