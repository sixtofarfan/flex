# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

class AccountHigherRep(models.TransientModel):
	_inherit = 'account.higher.rep'

	def get_report(self):
		filtro = []
		self.domain_dates()

		self.env.cr.execute("""
			CREATE OR REPLACE view account_higher_book as ("""+self._get_sql()+""")""")

		if self.account_ids:
			cuentas_list = []
			for i in self.account_ids:
				cuentas_list.append(i.code)
			filtro.append( ('cuenta','in',tuple(cuentas_list)) )

		if self.type_show == 'pantalla':
			return {
				'name': 'Libro Mayor Analitico',
				#'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.higher.book',
				'view_mode': 'tree,pivot,graph',
				'view_type': 'form',
			}

		if self.type_show == 'excel':
			return self.get_excel(filtro)
		
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

			if not direccion:
				raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')
			
			docname = 'LibroMayorAnalitico.csv'

			if self.account_ids:
				accounts_ids = self.account_ids.ids
				sql_accounts = " where account_id in (%s) " % (','.join(str(i) for i in accounts_ids))
				sql_query = """	COPY ("""+self._get_sql()+sql_accounts +""")TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			else:
				sql_query = """	COPY (select * from account_higher_book)TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			
			self.env.cr.execute(sql_query)

			#Caracteres Especiales
			import importlib
			import sys
			importlib.reload(sys)

			f = open(direccion + docname, 'rb')		

			return self.env['popup.it'].get_file(docname,base64.encodestring(b''.join(f.readlines())))

	@api.model
	def generate_view(self):
		self.env.cr.execute("""
			CREATE OR REPLACE view account_higher_book as (
				select row_number() OVER () AS id,
				f.periodo, f.fecha, f.libro, f.voucher, f.cuenta,
				f.debe, f.haber, f.balance, f.saldo, f.moneda, f.tc,
				f.code_cta_analitica, f.glosa, f.td_partner,f.doc_partner, f.partner, 
				f.td_sunat,f.nro_comprobante, f.fecha_doc, f.fecha_ven,
				aml.name as description,
				aml.ref as circular,
				fpr.name as payment_request,
				so.name as operation_number,
				so.internal_ref,
				so.internal_ref_child,
				('[' || pt.default_code || '] ' || pt.name) as product
				from fxo_get_mayor_detalle('{0}','{1}',{2}) as f
				left join account_move_line aml on aml.id = f.move_line_id
				left join fxo_payment_request fpr on fpr.id = aml.request_id
				left join sale_order so on so.id = aml.order_id
				left join product_product pp on pp.id = aml.product_id
				left join product_template pt on pt.id = pp.product_tmpl_id
			)
			""".format(
					date(date.today().year, 1, 1).strftime('%Y/%m/%d'),
					date(date.today().year, 12, 31).strftime('%Y/%m/%d'),
					self.env.company.id,
				)
		)

	def _get_sql(self):
		where = ''
		if self.account_ids:
			where = " where f.account_id in (%s) " % (','.join(str(i.id) for i in self.account_ids))
		if self.currency == 'pen':
			sql = """select row_number() OVER () AS id,
			f.periodo, f.fecha, f.libro, f.voucher, f.cuenta,
			f.debe, f.haber, f.balance, f.saldo, f.moneda, f.tc,
			f.code_cta_analitica, f.glosa, f.td_partner,f.doc_partner, f.partner, 
			f.td_sunat,f.nro_comprobante, f.fecha_doc, f.fecha_ven,
			aml.name as description,
			aml.ref as circular,
			fpr.name as payment_request,
			so.name as operation_number,
			so.internal_ref,
			so.internal_ref_child,
			('[' || pt.default_code || '] ' || pt.name) as product
			from fxo_get_mayor_detalle('%s','%s',%s) as f
			left join account_move_line aml on aml.id = f.move_line_id
			left join fxo_payment_request fpr on fpr.id = aml.request_id
			left join sale_order so on so.id = aml.order_id
			left join product_product pp on pp.id = aml.product_id
			left join product_template pt on pt.id = pp.product_tmpl_id
			%s
			""" % (
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				where,
			)
		else:
			sql = """select row_number() OVER () AS id,
			f.periodo, f.fecha, f.libro, f.voucher, f.cuenta,
			f.debe_me as debe, f.haber_me as haber, f.balance_me as balance, f.saldo_me as saldo, f.moneda, f.tc,
			f.code_cta_analitica, f.glosa, f.td_partner,f.doc_partner, f.partner, 
			f.td_sunat,f.nro_comprobante, f.fecha_doc, f.fecha_ven, 
			aml.name as description,
			aml.ref as circular,
			fpr.name as payment_request,
			so.name as operation_number,
			so.internal_ref,
			so.internal_ref_child,
			('[' || pt.default_code || '] ' || pt.name) as product
			from fxo_get_mayor_detalle('%s','%s',%s) as f
			left join account_move_line aml on aml.id = f.move_line_id
			left join fxo_payment_request fpr on fpr.id = aml.request_id
			left join sale_order so on so.id = aml.order_id
			left join product_product pp on pp.id = aml.product_id
			left join product_template pt on pt.id = pp.product_tmpl_id
			%s
			""" % (
				self.date_ini.strftime('%Y/%m/%d'),
				self.date_end.strftime('%Y/%m/%d'),
				str(self.company_id.id),
				where,
			)
		
		return sql

	def get_excel(self,filtro):
		import io
		from xlsxwriter.workbook import Workbook

		ReportBase = self.env['report.base']
		direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

		if not direccion:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

		workbook = Workbook(direccion +'Libro_Mayor_Analitico.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		##########LIBRO MAYOR ANALITICO############
		worksheet = workbook.add_worksheet("LIBRO MAYOR ANALITICO")
		worksheet.set_tab_color('blue')
		HEADERS = ['PERIODO','FECHA','LIBRO','VOUCHER','CUENTA','DEBE','HABER','BALANCE','SALDO','MON','TC',
				   'CTA ANALITICA','GLOSA','TDP','RUC','PARTNER','TD','NRO COMPROBANTE','FECHA DOC','FECHA VEN',
				   'SOLICITUD PAGO', 'NRO OPERACION', 'REFERENCIA INTERNA', 'REFERENCIA INTERNA HIJA', 'PRODUCTO',
				   'DESCRIPCION', 'CIRCULAR'
				   ]
		x=1
		worksheet = ReportBase.get_headers(worksheet,HEADERS,0,0,formats['boldbord'])

		for line in self.env['account.higher.book'].search(filtro):
			worksheet.write(x,0,line.periodo if line.periodo else '',formats['especial1'])
			worksheet.write(x,1,line.fecha if line.fecha else '',formats['dateformat'])
			worksheet.write(x,2,line.libro if line.libro else '',formats['especial1'])
			worksheet.write(x,3,line.voucher if line.voucher else '',formats['especial1'])
			worksheet.write(x,4,line.cuenta if line.cuenta else '',formats['especial1'])
			worksheet.write(x,5,line.debe if line.debe else '0.00',formats['numberdos'])
			worksheet.write(x,6,line.haber if line.haber else '0.00',formats['numberdos'])
			worksheet.write(x,7,line.balance if line.balance else '0.00',formats['numberdos'])
			worksheet.write(x,8,line.saldo if line.saldo else '0.00',formats['numberdos'])
			worksheet.write(x,9,line.moneda if line.moneda else '',formats['especial1'])
			worksheet.write(x,10,line.tc if line.tc else '0.0000',formats['numbercuatro'])
			worksheet.write(x,11,line.code_cta_analitica if line.code_cta_analitica else '',formats['especial1'])
			worksheet.write(x,12,line.glosa if line.glosa else '',formats['especial1'])
			worksheet.write(x,13,line.td_partner if line.td_partner else '',formats['especial1'])
			worksheet.write(x,14,line.doc_partner if line.doc_partner else '',formats['especial1'])
			worksheet.write(x,15,line.partner if line.partner else '',formats['especial1'])
			worksheet.write(x,16,line.td_sunat if line.td_sunat else '',formats['especial1'])
			worksheet.write(x,17,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
			worksheet.write(x,18,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
			worksheet.write(x,19,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
			worksheet.write(x,20,line.payment_request if line.payment_request else '',formats['especial1'])
			worksheet.write(x,21,line.operation_number if line.operation_number else '',formats['especial1'])
			worksheet.write(x,22,line.internal_ref if line.internal_ref else '',formats['especial1'])
			worksheet.write(x,23,line.internal_ref_child if line.internal_ref_child else '',formats['especial1'])
			worksheet.write(x,24,line.product if line.product else '',formats['especial1'])
			worksheet.write(x,25,line.description if line.description else '',formats['especial1'])
			worksheet.write(x,24,line.circular if line.circular else '',formats['especial1'])
			x += 1

		widths = [9,9,7,11,8,10,10,10,10,5,7,13,47,4,11,40,3,16,12,12] + 5 * [12]
		worksheet = ReportBase.resize_cells(worksheet,widths)
		workbook.close()

		f = open(direccion +'Libro_Mayor_Analitico.xlsx', 'rb')

		return self.env['popup.it'].get_file('Libro_Mayor_Analitico.xlsx',base64.encodestring(b''.join(f.readlines())))