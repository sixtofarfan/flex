# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date
from odoo.exceptions import UserError
import base64
from io import BytesIO
import re
import uuid

import codecs
import pprint

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch,cm,mm
from reportlab.lib.colors import magenta, red , black , blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.utils import simpleSplit
from reportlab.lib.enums import TA_JUSTIFY,TA_CENTER,TA_LEFT,TA_RIGHT
import time

class AccountJournalRep(models.TransientModel):
	_inherit = 'account.journal.rep'

	def _get_sql(self,content):
		sql_journals = "AND vst1.journal_id in (%s) " % (','.join(str(i) for i in self.libros.ids)) if content == 1 else ""

		if self.currency == 'pen':
			sql = """SELECT row_number() OVER () AS id, T.* FROM (SELECT
				vst1.periodo,vst1.fecha,vst1.libro,vst1.voucher,
				vst1.cuenta,vst1.debe,vst1.haber,vst1.balance,
				vst1.moneda,vst1.tc,vst1.importe_me,vst1.code_cta_analitica,
				vst1.glosa,vst1.td_partner,vst1.doc_partner,vst1.partner,
				vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
				vst1.col_reg,vst1.monto_reg,vst1.medio_pago,vst1.ple_diario,
				vst1.ple_compras,vst1.ple_ventas,vst1.registro, array_to_string(vst1.analytic_tag_names,',','*') as analytic_tag_names,
				aml.name as description,
				aml.ref as circular
				FROM vst_diariog vst1
				INNER JOIN account_move_line aml on aml.id = vst1.move_line_id
				WHERE (vst1.fecha between '%s' AND '%s')
				AND vst1.company_id = %s %s)T
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				sql_journals)
		else:
			sql = """SELECT row_number() OVER () AS id, T.* FROM (SELECT
				vst1.periodo,vst1.fecha,vst1.libro,vst1.voucher,
				vst1.cuenta,vst2.debe_me as debe ,vst2.haber_me as haber,(vst2.debe_me - vst2.haber_me) as balance,
				vst1.moneda,vst1.tc,vst1.importe_me,vst1.code_cta_analitica,
				vst1.glosa,vst1.td_partner,vst1.doc_partner,vst1.partner,
				vst1.td_sunat,vst1.nro_comprobante,vst1.fecha_doc,vst1.fecha_ven,
				vst1.col_reg,vst1.monto_reg,vst1.medio_pago,vst1.ple_diario,
				vst1.ple_compras,vst1.ple_ventas,vst1.registro, array_to_string(vst1.analytic_tag_names,',','*') as analytic_tag_names,
				aml.name as description,
				aml.ref as circular
				FROM vst_diariog vst1
				INNER JOIN account_move_line aml on aml.id = vst1.move_line_id
				LEFT JOIN vst_diariog_me vst2 on vst2.move_id = vst1.move_id and vst2.move_line_id = vst1.move_line_id
				WHERE (vst1.fecha between '%s' AND '%s')
				AND vst1.company_id = %s %s)T
			""" % (self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				sql_journals)
		return sql

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']

		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libro_Diario.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO DIARIO############
		worksheet = workbook.add_worksheet("LIBRO DIARIO")
		worksheet.set_tab_color('blue')

		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','MON','TC','IMP ME',
		'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMP','FECHA DOC','FECHA VEN','COL REG','MONTO REG','MED PAGO',
		'PLE DIARIO','PLE COMPRAS','PLE VENTAS','ETIQUETAS ANALITICAS', 'DESCRIPTION', 'CIRCULAR']
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1

		for line in self.env['account.journal.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,9,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,10,line.importe_me if line.importe_me else '0.00',formats['numberdos'])
			worksheet.write(x,11,line.code_cta_analitica if line.code_cta_analitica else '',formats['especial1'])
			worksheet.write(x,12,line.glosa if line.glosa else '',formats['especial1'])
			worksheet.write(x,13,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,14,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,15,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,16,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,17,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,18,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,19,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,20,line.col_reg if line.col_reg else '',formats['especial1'])
			worksheet.write(x,21,line.monto_reg if line.monto_reg else '0.00',formats['numberdos'])
			worksheet.write(x,22,line.medio_pago if line.medio_pago else '',formats['especial1'])
			worksheet.write(x,23,line.ple_diario if line.ple_diario else '',formats['especial1'])
			worksheet.write(x,24,line.ple_compras if line.ple_compras else '',formats['especial1'])
			worksheet.write(x,25,line.ple_ventas if line.ple_ventas else '',formats['especial1'])
			worksheet.write(x,26,line.analytic_tag_names if line.analytic_tag_names else '',formats['especial1'])
			worksheet.write(x, 27, line.description if line.description else '', formats['especial1'])
			worksheet.write(x, 28, line.circular if line.circular else '', formats['especial1'])
			x += 1

		widths = [9,9,7,11,8,10,10,10,5,7,11,13,47,4,11,40,3,16,12,12,12,12,12,12,12,12,25]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libro_Diario.xlsx', 'rb')
		return self.env['popup.it'].get_file('Libro Diario.xlsx',base64.encodestring(b''.join(f.readlines())))