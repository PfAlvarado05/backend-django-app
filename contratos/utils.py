from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.units import cm
from django.conf import settings
import os
from .models import Semana, RegistroDiario, DiaNoLaborable, Gasto

def generar_reporte_pdf_semanal(contrato, semana_numero):
    semana = Semana.objects.get(contrato=contrato, numero_semana=semana_numero)
    registros = RegistroDiario.objects.filter(semana=semana)
    dias_no = DiaNoLaborable.objects.filter(contrato=contrato, fecha__range=[semana.fecha_inicio, semana.fecha_fin])
    gastos = Gasto.objects.filter(semana=semana)

    ruta_archivo = os.path.join(settings.MEDIA_ROOT, f"reporte_contrato_{contrato.id}_semana_{semana_numero}.pdf")
    c = canvas.Canvas(ruta_archivo, pagesize=A4)
    width, height = A4

    def nueva_pagina():
        c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 2 * cm, f"Reporte Semanal - Semana {semana_numero}")
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 2.7 * cm, f"Contrato: {contrato.nombre}")
        return height - 4 * cm

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2 * cm, f"Reporte Semanal - Semana {semana_numero}")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 2.7 * cm, f"Contrato: {contrato.nombre}")

    y = height - 4 * cm
    trabajadores = contrato.trabajadores.all()
    for trabajador in trabajadores:
        if y < 6 * cm:
            y = nueva_pagina()

        c.setFont("Helvetica-Bold", 13)
        c.drawString(2 * cm, y, f"Trabajador: {trabajador.nombre}")
        y -= 1 * cm

        datos = [["Día", "Unidades", "Pago (Bs)"]]
        total_unidades = 0
        total_pago = 0

        registros_trabajador = registros.filter(trabajador=trabajador).order_by('dia')
        ya_vistos = set()
        for reg in registros_trabajador:
            clave = (reg.dia, reg.trabajador.id)
            if clave in ya_vistos:
                continue  # evitar duplicados
            ya_vistos.add(clave)

            dia = reg.dia.capitalize()
            pago = reg.unidades * contrato.precio_trato
            datos.append([dia, str(reg.unidades), f"{pago:.2f}"])
            total_unidades += reg.unidades
            total_pago += pago

        datos.append(["Total", str(total_unidades), f"{total_pago:.2f}"])

        tabla = Table(datos, colWidths=[6 * cm, 4 * cm, 4 * cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ]))

        height_tabla = len(datos) * 0.6 * cm + 1 * cm
        if y - height_tabla < 4 * cm:
            y = nueva_pagina()

        tabla.wrapOn(c, width, height)
        tabla.drawOn(c, 2 * cm, y - len(datos) * 0.6 * cm)
        y -= (len(datos) + 1.5) * 0.6 * cm

    if dias_no.exists():
        if y < 6 * cm:
            y = nueva_pagina()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2 * cm, y, "Días no laborables:")
        y -= 0.7 * cm
        for dia in dias_no:
            if y < 3 * cm:
                y = nueva_pagina()
            c.setFont("Helvetica", 11)
            c.drawString(2.5 * cm, y, f"{dia.fecha} - {dia.razon}")
            y -= 0.5 * cm

    if gastos.exists():
        if y < 6 * cm:
            y = nueva_pagina()
        c.setFont("Helvetica-Bold", 12)
        y -= 1 * cm
        c.drawString(2 * cm, y, "Gastos registrados:")
        y -= 0.7 * cm
        for gasto in gastos:
            if y < 3 * cm:
                y = nueva_pagina()
            c.setFont("Helvetica", 11)
            c.drawString(2.5 * cm, y, f"{gasto.nombre}: Bs {gasto.costo:.2f}")
            y -= 0.5 * cm

    c.save()
    return ruta_archivo
