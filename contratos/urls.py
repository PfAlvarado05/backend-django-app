from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    ContratoListCreateView,
    TrabajadorListCreateView,
    GastoListCreateView,
    SemanaListView,
    RegistroDiarioListCreateView,
    DiaNoLaborableListCreateView,
    GastoPorSemanaListCreateView,
    generar_pdf_reporte_semana,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('contratos/', ContratoListCreateView.as_view(), name='contrato-list-create'),
    path('contratos/<int:contrato_id>/trabajadores/', TrabajadorListCreateView.as_view(), name='trabajador-list-create'),
    path('contratos/<int:contrato_id>/gastos/', GastoListCreateView.as_view(), name='gasto-list-create'),
    path('contratos/<int:contrato_id>/semanas/', SemanaListView.as_view(), name='semana-list'),
    path('contratos/<int:contrato_id>/registro/', RegistroDiarioListCreateView.as_view(), name='registro_diario'),
    path('contratos/<int:contrato_id>/dias_no_laborables/', DiaNoLaborableListCreateView.as_view(), name='dia-no-laborable-list-create'),
    path('semanas/<int:semana_id>/gastos/', GastoPorSemanaListCreateView.as_view(), name='gasto-semana-list-create'),

    path('contratos/<int:contrato_id>/reporte_pdf/', generar_pdf_reporte_semana, name='reporte-pdf'),
]
