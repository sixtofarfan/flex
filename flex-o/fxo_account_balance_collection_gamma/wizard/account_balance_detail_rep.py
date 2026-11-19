# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountBalanceDetailRep(models.TransientModel):
	_inherit = 'account.balance.detail.rep'

	def get_report(self):
		sql_partner = """"""
		sql_account = """"""
		sql_type_acc = """"""
		
		if self.only_pending:
			only_pendd = 1
		else:
			only_pendd = 0

		if self.partner_id:
			sql_partner = """and a1.partner_id = %s""" % (self.partner_id.id)
		if self.account_id:
			sql_account = """and a1.account_id = %s""" % (self.account_id.id)
		if self.type_account:
			sql_type_acc = """and a3.type = '%s'""" % (self.type_account)

		sql = """
			CREATE OR REPLACE view account_balance_detail_book as (SELECT row_number() OVER () AS id,a1.* FROM get_fxo_saldo_detalle_gamma('%s','%s',%s) a1 
			LEFT JOIN account_account a2 ON a2.id = a1.account_id
			LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
			WHERE concat(a1.partner_id,a1.account_id,a1.td_sunat,a1.nro_comprobante) in(
			SELECT concat(partner_id,account_id,td_sunat,nro_comprobante) FROM get_saldos('%s','%s',%s,%s)) %s %s %s)""" % (
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				str(only_pendd),
				sql_partner,
				sql_account,
				sql_type_acc
			)

		self.env.cr.execute(sql)

		if self.type_show == 'pantalla':
			return {
				'name': 'Detalle Comprobantes',
				'type': 'ir.actions.act_window',
				'res_model': 'account.balance.detail.book',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.type_show == 'excel':
			return self.get_excel()

	def get_excel(self):
		import io
		from xlsxwriter.workbook import Workbook
		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Detalle_Comprobantes.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Detalle Comprobantes")
		worksheet.set_tab_color('blue')

		HEADERS = [
			'PERIODO','FECHA','LIBRO','VOUCHER','TDP','RUC','PARTNER','COBRADOR','SOLICITANTE','PERIODO FACTURACION','TD','NRO COMP',
			'FEC DOC','FEC VEN','CUENTA','DEBE','HABER','BALANCE','IMPORTE ME','SALDO MN','SALDO ME', 'SOLICITUD PAGO', 
			'NRO OPERACION', 'REFERENCIA INTERNA', 'REFERENCIA INTERNA HIJA', 'PRODUCTO'
			]
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])
		x=1
		#Totals#
		debe, haber, balance, importe_me = 0, 0, 0, 0

		for line in self.env['account.balance.detail.book'].search([]):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,5,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,6,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,7,line.collection if line.collection else '',formats['especial1'])
			worksheet.write(x,8,line.user_request if line.user_request else '',formats['especial1'])
			worksheet.write(x,9,line.invoice_period if line.invoice_period else '',formats['especial1'])
			worksheet.write(x,10,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,11,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,12,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,13,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,14,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,15,line.debe if line.debe else 0,formats['numberdos'])
			worksheet.write(x,16,line.haber if line.haber else 0,formats['numberdos'])
			worksheet.write(x,17,line.balance if line.balance else 0,formats['numberdos'])
			worksheet.write(x,18,line.importe_me if line.importe_me else 0,formats['numberdos'])
			worksheet.write(x,19,line.saldo if line.saldo else 0,formats['numberdos'])
			worksheet.write(x,20,line.saldo_me if line.saldo_me else 0,formats['numberdos'])
			worksheet.write(x,21,line.payment_request if line.payment_request else '',formats['especial1'])
			worksheet.write(x,22,line.operation_number if line.operation_number else '',formats['especial1'])
			worksheet.write(x,23,line.internal_ref if line.internal_ref else '',formats['especial1'])
			worksheet.write(x,24,line.internal_ref_child if line.internal_ref_child else '',formats['especial1'])
			worksheet.write(x,25,line.product if line.product else '',formats['especial1'])
			x += 1
			debe += line.debe if line.debe else 0
			haber += line.haber if line.haber else 0
			balance += line.balance if line.balance else 0
			importe_me += line.importe_me if line.importe_me else 0

		worksheet.write(x,15,debe,formats['numbertotal'])
		worksheet.write(x,16,haber,formats['numbertotal'])
		worksheet.write(x,17,balance,formats['numbertotal'])
		worksheet.write(x,18,importe_me,formats['numbertotal'])

		widths = [7,10,10,10,4,11,40,20,20,20,4,10,10,10,10,12,12,12,12,12,12] + 5 * [12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()
		f = open(direccion +'Detalle_Comprobantes.xlsx', 'rb')
		return self.env['popup.it'].get_file('Detalle_Comprobantes.xlsx',base64.encodestring(b''.join(f.readlines())))