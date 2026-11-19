# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from datetime import *
from odoo.exceptions import UserError
import base64

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.colors import magenta, red, black, blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
import time


class MaturityAnalysisDollarsRep(models.TransientModel):
    _name = 'maturity.analysis.dollars.rep'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string=u'Compañia', required=True,
                                 default=lambda self: self.env.company, readonly=True)
    date = fields.Date(string=u'Fecha', required=True, default=fields.Date.context_today)
    type_show = fields.Selection([('pantalla', 'Pantalla'), ('excel', 'Excel'), ('pdf', 'PDF')], string=u'Mostrar en',
                                 default='pantalla')
    mayor = fields.Char(string='Mayor', size=2,
                        help='Escriba los dos primeros digitos de que la cuenta que desea filtrar.')
    currency_rate = fields.Float(string='Tipo de Cambio', digits=(12, 4))

    def get_receivable(self):
        return self.get_report('receivable')

    def get_payable(self):
        return self.get_report('payable')

    def get_report(self, type):
        first_date = date(self.date.year, 1, 1)
        tools.drop_view_if_exists(self._cr, 'maturity_analysis_dollars_book')
        self.env.cr.execute("""
			CREATE OR REPLACE view maturity_analysis_dollars_book as (""" + self._get_sql(first_date, self.date,
                                                                                          self.company_id.id, type,
                                                                                          self.mayor) + """)""")

        if self.type_show == 'pantalla':
            return {
                'name': 'Analisis de Vencimiento',
                'type': 'ir.actions.act_window',
                'res_model': 'maturity.analysis.dollars.book',
                'view_mode': 'tree',
                'view_type': 'form',
                'views': [(False, 'tree')],
            }

        if self.type_show == 'excel':
            return self.get_excel()

        if self.type_show == 'pdf':
            return self.getPdf()

    def _get_sql(self, first_date, end_date, company_id, type, mayor):
        sql_mayor = ""
        if mayor:
            sql_mayor = "WHERE left(cuenta,2) = '%s' " % (mayor)

        sql = """SELECT row_number() OVER () AS id,*
				FROM get_fxo_maturity_analysis_dollars('%s','%s',%s,'%s',%d)
				%s
			""" % (first_date.strftime('%Y/%m/%d'),
                   end_date.strftime('%Y/%m/%d'),
                   str(company_id),
                   str(type),
                   self.currency_rate,
                   sql_mayor)
        print(sql)
        return sql

    def get_excel(self):
        import io
        from xlsxwriter.workbook import Workbook
        ReportBase = self.env['report.base']

        direccion = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
                                                      limit=1).dir_create_file

        if not direccion:
            raise UserError(
                u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

        workbook = Workbook(direccion + 'Analisis_Vencimientos.xlsx')
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        ##########ANALISIS VENCIMIENTO############
        worksheet = workbook.add_worksheet("ANALISIS VENCIMIENTO")
        worksheet.set_tab_color('blue')

        HEADERS = ['PARTNER', 'COBRADOR', 'INVOICE USER', 'EXPO USER', 'LIMITE DE CREDITO',
                   'TERMINO DE PAGO', 'TOTAL GENERAL', 'TOTAL DEUDA SIN VENCER', 'TOTAL DEUDA VENCIDA',
                   u'1 - 7', u'8 - 15', u'16 - 30', u'31 - 60', u'61 - 90', u'91 - MÁS']
        worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
        x = 1

        for line in self.env['maturity.analysis.dollars.book'].search([]):
            worksheet.write(x, 0, line.partner if line.partner else '', formats['especial1'])
            worksheet.write(x, 1, line.collection if line.collection else '', formats['especial1'])
            worksheet.write(x, 2, line.invoice_user_id if line.invoice_user_id else '', formats['especial1'])
            worksheet.write(x, 3, line.invoice_expo_user_id if line.invoice_expo_user_id else '', formats['especial1'])
            worksheet.write(x, 4, line.credit_limit if line.credit_limit else '0.00', formats['numberdos'])
            worksheet.write(x, 5, line.payment_term_id.name if line.payment_term_id else '', formats['especial1'])
            worksheet.write(x, 6, line.total if line.total else '0.00', formats['numberdos'])
            worksheet.write(x, 7, line.whithout_debt if line.whithout_debt else '0.00', formats['numberdos'])
            worksheet.write(x, 8, line.debt if line.debt else '0.00', formats['numberdos'])
            worksheet.write(x, 9, line.between_1_7 if line.between_1_7 else '0.00', formats['numberdos'])
            worksheet.write(x, 10, line.between_8_15 if line.between_8_15 else '0.00', formats['numberdos'])
            worksheet.write(x, 11, line.between_16_30 if line.between_16_30 else '0.00', formats['numberdos'])
            worksheet.write(x, 12, line.between_31_60 if line.between_31_60 else '0.00', formats['numberdos'])
            worksheet.write(x, 13, line.between_61_90 if line.between_61_90 else '0.00', formats['numberdos'])
            worksheet.write(x, 14, line.between_91_more if line.between_91_more else '0.00', formats['numberdos'])
            x += 1

        widths = [40, 20, 20, 20] + [12] * 9
        worksheet = ReportBase.resize_cells(worksheet, widths)
        workbook.close()

        f = open(direccion + 'Analisis_Vencimientos.xlsx', 'rb')
        return self.env['popup.it'].get_file('Analisis_Vencimientos.xlsx', base64.encodestring(b''.join(f.readlines())))

    def _get_header_report(self):
        headers = ['PARTNER', 'COBRADOR', 'INVOICE USER', 'EXPO USER', 'LIMITE DE CREDITO',
                   'TERMINO DE PAGO', 'TOTAL GENERAL', 'TOTAL DEUDA SIN VENCER', 'TOTAL DEUDA VENCIDA',
                   u'1 - 7', u'8 - 15', u'16 - 30', u'31 - 60', u'61 - 90', u'91 - MÁS']

        return headers

    def getPdf(self):
        # CREANDO ARCHIVO PDF
        direccion = self.env['main.parameter'].search([('company_id', '=', self.company_id.id)],
                                                      limit=1).dir_create_file

        if not direccion:
            raise UserError(
                u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

        name_file = "Analisis_Vencimientos.pdf"

        archivo_pdf = SimpleDocTemplate(str(direccion) + name_file, pagesize=(2200, 1000), rightMargin=15,
                                        leftMargin=15, topMargin=40, bottomMargin=30)

        elements = []
        style_title = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=40, fontName="Helvetica")
        style_form = ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=24, fontName="Helvetica")
        style_left = ParagraphStyle(name='Left', alignment=TA_LEFT, fontSize=14, fontName="Helvetica")
        style_right = ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=14, fontName="Helvetica")
        style_title_tab = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=15, fontName="Helvetica-Bold")

        company = self.company_id
        texto = u'Nombre de la Compañía: ' + (company.name)
        elements.append(Paragraph(texto, style_form))
        elements.append(Spacer(1, 12))
        texto = u'Ruc de la Compañía: ' + (company.vat if company.vat else '')
        elements.append(Paragraph(texto, style_form))
        elements.append(Spacer(1, 12))
        texto = 'A Fecha: ' + str(self.date)
        elements.append(Paragraph(texto, style_form))
        elements.append(Spacer(1, 40))

        headers = ['PARTNER', 'COBRADOR', 'INVOICE USER', 'EXPO USER', 'LIMITE DE CREDITO',
                   'TERMINO DE PAGO', 'TOTAL', 'SIN VENCER', 'VENCIDA',
                   u'1 - 7', u'8 - 15', u'16 - 30', u'31 - 60', u'61 - 90', u'91 - MÁS']

        datos = []
        datos.append([])

        for i in headers:
            datos[0].append(Paragraph(i, style_title_tab))

        for c, fila in enumerate(self.env['maturity.analysis.dollars.book'].search([])):
            account_payment_term = self.env['account.payment.term'].search([('id', '=', fila['payment_term_id'].id)])
            datos.append([])
            datos[c + 1].append(Paragraph((fila['partner']) if fila['partner'] else '', style_left))
            datos[c + 1].append(Paragraph((fila['collection']) if fila['collection'] else '', style_left))
            datos[c + 1].append(Paragraph((fila['invoice_user_id']) if fila['invoice_user_id'] else '', style_left))
            datos[c + 1].append(
                Paragraph((fila['invoice_expo_user_id']) if fila['invoice_expo_user_id'] else '', style_left))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['credit_limit'])) if fila['credit_limit'] else '0.00', style_right))
            datos[c + 1].append(Paragraph((account_payment_term.name) if account_payment_term else '', style_left))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['total'])) if fila['total'] else '0.00', style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['whithout_debt'])) if fila['whithout_debt'] else '0.00',
                          style_right))
            datos[c + 1].append(Paragraph(str("{:.2f}".format(fila['debt'])) if fila['debt'] else '0.00', style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_1_7'])) if fila['between_1_7'] else '0.00', style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_8_15'])) if fila['between_8_15'] else '0.00', style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_16_30'])) if fila['between_16_30'] else '0.00',
                          style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_31_60'])) if fila['between_31_60'] else '0.00',
                          style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_61_90'])) if fila['between_61_90'] else '0.00',
                          style_right))
            datos[c + 1].append(
                Paragraph(str("{:.2f}".format(fila['between_91_more'])) if fila['between_91_more'] else '0.00',
                          style_right))

        table_datos = Table(datos, colWidths=[15 * cm] + [6 * cm] * 5 + [3 * cm] * 9, rowHeights=len(datos) * [1 * cm])

        color_cab = colors.Color(red=(220 / 255), green=(230 / 255), blue=(241 / 255))

        # Estilo de Tabla
        style_table = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), color_cab),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ])
        table_datos.setStyle(style_table)

        elements.append(table_datos)

        # Build
        archivo_pdf.build(elements)

        # Caracteres Especiales
        import importlib
        import sys
        importlib.reload(sys)
        import os

        f = open(str(direccion) + name_file, 'rb')
        return self.env['popup.it'].get_file(name_file, base64.encodestring(b''.join(f.readlines())))
