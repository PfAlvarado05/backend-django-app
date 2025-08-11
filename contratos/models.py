from django.db import models
from django.contrib.auth.models import User

class Contrato(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    oficio = models.CharField(max_length=100)
    precio_real = models.FloatField()
    precio_trato = models.FloatField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    impuesto_porcentaje = models.FloatField()
    porcentaje_ganancia = models.FloatField()
    max_trabajadores = models.IntegerField()

    def calcular_ganancia(self):
        total_unidades = sum(
            semana.total_unidades() for semana in self.semanas.all()
        )
        ingreso_teorico = total_unidades * self.precio_real
        pagos_trabajadores = total_unidades * self.precio_trato
        impuestos = ingreso_teorico * (self.impuesto_porcentaje / 100)
        gastos = sum(semana.total_gastos() for semana in self.semanas.all())

        return ingreso_teorico - pagos_trabajadores - impuestos - gastos

    @property
    def ganancia_neta(self):
        return self.calcular_ganancia()

    def duracion_semanas(self):
        dias = (self.fecha_fin - self.fecha_inicio).days
        return (dias + 6) // 7

    def __str__(self):
        return self.nombre

class Trabajador(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='trabajadores')
    nombre = models.CharField(max_length=100)
    oficio = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Semana(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='semanas')
    numero_semana = models.IntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()

    def total_unidades(self):
        return sum(r.unidades for r in self.registros.all())

    def total_pago(self):
        return sum(r.unidades * r.trabajador.contrato.precio_trato for r in self.registros.all())

    def total_gastos(self):
        return sum(g.costo for g in self.gastos.all())

    def __str__(self):
        return f"Semana {self.numero_semana} ({self.fecha_inicio} - {self.fecha_fin})"

class RegistroDiario(models.Model):
    semana = models.ForeignKey(Semana, on_delete=models.CASCADE)
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE)
    dia = models.CharField(max_length=10)
    unidades = models.PositiveIntegerField(default=0)

    def pago_total(self):
        return self.unidades * self.semana.contrato.precio_trato
class DiaNoLaborable(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='dias_no_laborables')
    fecha = models.DateField()
    razon = models.CharField(max_length=255, default="No especificado")

    def __str__(self):
        return f"{self.fecha} - {self.razon}"

class Gasto(models.Model):
    contrato = models.ForeignKey(Contrato, on_delete=models.CASCADE, related_name='gastos')
    semana = models.ForeignKey(Semana, on_delete=models.CASCADE, related_name='gastos', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    costo = models.FloatField()

    def __str__(self):
        if self.semana:
            return f"[Semana {self.semana.numero_semana}] {self.nombre} - Bs {self.costo}"
        return f"{self.nombre} - Bs {self.costo}"

