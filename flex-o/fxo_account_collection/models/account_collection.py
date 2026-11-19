# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
from collections import *

class AccountCollection(models.Model):
	_name = 'account.collection'
	_description = 'Account Collection'
	_order = 'date desc'

	name = fields.Char(string='Nombre', default='/', readonly=True, required=True)
	journal_id = fields.Many2one('account.journal', string='Diario', required=True, domain=[('type', '=', 'bank')],
		states={'cofirmed': [('readonly', True)]})
	type = fields.Selection(related='journal_id.bank_id.format_bank', string='Banco', store=True)
	date = fields.Date(string='Fecha', default=fields.Date.today(), required=True, states={'cofirmed': [('readonly', True)]})
	collection_type = fields.Selection([
		('shipping', 'Envio'),
		('charge', 'Cobro'),
	], string='Tipo de Proceso', required=True, states={'cofirmed': [('readonly', True)]})
	record_ids = fields.One2many('account.collection.record', 'collection_id', readonly=True)
	output_name = fields.Char(string='Nombre del Archivo')
	file = fields.Binary(string='Archivo', readonly=True, filename='output_name')
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, readonly=True)
	state = fields.Selection([
		('draft', 'Borrador'),
		('confirmed', 'Confirmado'),
	], string='Estado', default='draft', required=True)

	@api.constrains('journal_id')
	def verify_bank_type(self):
		for rec in self:
			if rec.type not in ['bbva', 'bcp', 'scotiabank']:
				raise UserError('No se puede utilizar un banco que tenga formato diferente a bcp o scotiabank')

	def set_draft(self):
		self.state = 'draft'
		self.name = '/'
		for rec in self.record_ids:
			rec.payment_id.action_draft()

	def set_confirmed(self):
		if self.collection_type == 'charge':
			if not self.record_ids:
				raise UserError('Es necesario tener lineas para confirmar')
			for rec in self.record_ids:
				try:
					rec.payment_id.post()
				except:
					raise UserError('El documento %s no pudo procesarse es probable que ya este cancelado o el Diario debe tener una secuencia Unica x CIA ' % rec.move_id.ref)
		self.state = 'confirmed'
		self.name = self.env['ir.sequence'].next_by_code('seq_account_collection') or '/'

	def get_collection_import(self):
		return {
			'name': 'Importacion',
			'type': 'ir.actions.act_window',
			'res_model': 'account.collection.wizard',
			'views': [(self.env.ref('fxo_account_collection.view_account_collection_wizard_import').id, 'form')],
			'context': self._context,
			'target': 'new',
		}

	def delete_special_chars(self, _string):
		import string
		normal_chars = list(string.ascii_letters)
		normal_chars += list(string.digits)
		normal_chars.append(' ')
		special_chars = {
			'Ñ':'N', 'ñ':'n', 'Á':'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U', 'á':'a', 'é':'e', 'í':'i',
			'ó':'o', 'ú':'u', 'Ü':'U', 'ü':'u', '@':'a', ':':'', 'Ã':'A', '`':'', '“':'',
		}
		new_str = _string
		for l in _string:
			if l in special_chars.keys():
				new_str = new_str.replace(l, special_chars[l])
			elif l not in normal_chars:
				new_str = new_str.replace(l, '')
		return new_str

	def generate_xls_collection(self):
		import io, base64
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		route = MainParameter.dir_create_file
		if not route:
			raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Nomina para su Compañía')
		if self.type == 'bcp':
			bank = 'BCP'  
		elif self.type == 'scotiabank': 
			bank = 'Scotiabank'
		else:
			bank = 'BBVA'
		currency = 'USD' if self.journal_id.currency_id.name == 'USD' else 'PEN'
		mon = 2 if currency == 'USD' else 162
		Moves = self.env['account.move'].search([
			('type', '=', 'out_invoice'),
			('invoice_payment_state', '=', 'not_paid'),
			('state', '=', 'posted'),
			('currency_id.name', '=', currency),
		], order='partner_id, invoice_period_id')

		doc_name = 'Recaudacion %s %s.xlsx' % (bank, currency)
		workbook = Workbook(route + doc_name)

		ReportBase = self.env['report.base']
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)
		worksheet = workbook.add_worksheet('Recaudacion' + bank + currency)
		worksheet.set_tab_color('green')
		if self.type == 'bcp':
			sql = """
				select
				coalesce(res.ref,'')  as Codigo,
				res.display_name as Nombre,
				concat(replace(amo.ref,'-','N'),'SERV',
				(case extract(MONTH FROM amo.invoice_date_due) when 1 then 'ENE'
				when 2 then 'FEB' 
				when 3 then 'MAR' 
				when 4 then 'ABR' 
				when 5 then 'MAY' 
				when 6 then 'JUN' 
				when 7 then 'JUL' 
				when 8 then 'AGO' 
				when 9 then 'SEP' 
				when 10 then 'OCT' 
				when 11 then 'NOV' 
				when 12 then 'DIC' end),extract(YEAR FROM amo.invoice_date_due)) as InfoRetorno, 
				amo.invoice_date as Emision, 
				amo.invoice_date_due as Vencimiento, 
				amo.amount_residual as MontoaPagar, 
				replace(amo.ref,'-','N') as NumDocumento, 
				res.vat as DocIdentidad 
				from account_move amo 
				inner join einvoice_catalog_01 ec1 on  ec1.id = amo.type_document_id 
				inner join res_partner res on amo.partner_id = res.id 
				WHERE amo.type in ('out_refund','out_invoice') 
				and amo.amount_residual > 0 
				and amo.currency_id = %s
				and ec1.code <> '07'
				and amo.state = 'posted'
				order by res.display_name,amo.invoice_date
			""" % mon
			self._cr.execute(sql)
			rows = self._cr.fetchall()
			codigo_old = ''
			periodo_old = ''
			periodo = ''

			#Crear archivo en excel
			#wb = xlsxwriter.Workbook('Temporal.xlsx')
			#ws = wb.add_worksheet('bcp_soles')

			# Add a number format for cells with money.
			number_format = workbook.add_format({'num_format': '#,##0.00'})

			# Add an Excel date format.
			date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

			#base_vencimiento = date(anio, mes, dia)

			#se empieza por la celda con fila y columna en CERO
			fila = 0
			columna = 0

			#llenado de cabecera de columnas
			worksheet.write(fila, columna,     'CODIGO DEL DEPOSITANTE')
			worksheet.write(fila, columna + 1, 'NOMBRE DEL DEPOSITANTE')
			worksheet.write(fila, columna + 2, 'INFORMACION DE RETORNO')
			worksheet.write(fila, columna + 3, 'FECHA DE EMISION')
			worksheet.write(fila, columna + 4, 'FECHA DE VENCIMIENTO')
			worksheet.write(fila, columna + 5, 'MONTO A PAGAR')
			worksheet.write(fila, columna + 6, 'MORA/CARGO FIJO')
			worksheet.write(fila, columna + 7, 'MONTO MINIMO')
			worksheet.write(fila, columna + 8, 'TIPO DE REGISTRO')
			worksheet.write(fila, columna + 9, 'NRO DOCUMENTO DE PAGO')
			worksheet.write(fila, columna + 10, 'NRO DOCUMENTO DE IDENTIDAD')
			fila = fila + 1

			cuenta = 1
			registro = 1

			for row in rows:
				codigo = row[0]
				nombre = row[1][0:39]
				informacion = row[2]
				emision_d = row[3]
				if not emision_d:
					raise UserError('No tiene fecha emision en el documento: ' + row[6])
				montopagar = row[5]
				numdocumento = row[6]
				docidentidad = row[7]

				nombre = nombre.replace('Á','A')
				nombre = nombre.replace('É','E')
				nombre = nombre.replace('Í','I')
				nombre = nombre.replace('Ó','O')
				nombre = nombre.replace('Ú','U')
				nombre = nombre.replace('Ñ','N')

				nombre = nombre.replace('á','a')
				nombre = nombre.replace('í','i')
				nombre = nombre.replace('ó','o')
				nombre = nombre.replace('ú','u')
				nombre = nombre.replace('é','e')
				nombre = nombre.replace('ñ','n')

				nombre = nombre.replace('*','')
				nombre = nombre.replace('-','')
				nombre = nombre.replace('/','')
				nombre = nombre.replace('#','')
				nombre = nombre.replace('(','')
				nombre = nombre.replace(')','')
				nombre = nombre.replace('+','')
				nombre = nombre.replace('&','')

				nombre = nombre.replace('"','')
				nombre = nombre.replace('´','')
				nombre = nombre.replace("'","")
				nombre = nombre.replace("`","")
				nombre = nombre.replace("@","")

				anio = emision_d.year
				mes = emision_d.month
				dia = 0

				if mes == 1 or mes == 3 or mes == 5 or mes == 7 or mes == 8 or mes == 10 or mes == 12:
					dia = 31
				elif mes == 4 or mes == 6 or mes == 9 or mes == 11:
					dia = 30
				elif mes == 2:
					residuo = anio % 4
					if residuo == 0:
						dia = 29
					else:
						dia = 28

				base_vencimiento = date(anio,mes,dia)

				periodo = emision_d.strftime('%Y%m')
				emision_t = emision_d.strftime('%d/%m/%Y')



				if codigo_old != codigo:
					print('cambio de cliente ' + str(codigo))
					vencimiento_d2 = base_vencimiento
				else:
					if periodo != periodo_old :
						vencimiento_d2 = base_vencimiento
					else:
						vencimiento_d2 = vencimiento_d2 - timedelta(days=1)

				vencimiento_t = vencimiento_d2.strftime('%d-%m-%Y')

				#llenado de cada celda con datos
				worksheet.write(fila, columna, codigo)
				worksheet.write(fila, columna + 1, nombre)
				worksheet.write(fila, columna + 2, informacion)
				worksheet.write_datetime(fila, columna + 3, emision_d,date_format)
				worksheet.write_datetime(fila, columna + 4, vencimiento_d2,date_format)
				worksheet.write_number(fila, columna + 5, round(montopagar,2),number_format)
				worksheet.write_number(fila, columna + 6, 0,number_format)
				worksheet.write_number(fila, columna + 7, 0,number_format)
				worksheet.write(fila, columna + 8, '')
				worksheet.write(fila, columna + 9, str(numdocumento))
				worksheet.write(fila, columna + 10, str(docidentidad))
                                #worksheet.write(fila, columna + 10, str(docidentidad.rstrip()))
				fila = fila + 1
				registro = registro + 1
				codigo_old = codigo
				periodo_old = periodo

			widths = [12, 40, 20, 12, 12, 12, 12, 12, 14, 14, 14]
			worksheet = ReportBase.resize_cells(worksheet, widths)

			# months = ['', 'ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SET', 'OCT', 'NOV', 'DIC']
			# if Moves:
			# 	Partners = list(dict.fromkeys(Moves.mapped('partner_id').ids))
			# 	print('PARTNERS', Partners)
			# 	all_dates = {}
			# 	for c, partner in enumerate(Partners):
			# 		fil_moves = Moves.filtered(lambda m: m.partner_id.id == partner)
			# 		print('fil_moves', fil_moves)
			# 		last_period, last_date, x = None, None, 0
			# 		for move in fil_moves:
			# 			print('move', move)
			# 			if move.invoice_period_id:
			# 				if last_period != move.invoice_period_id:
			# 					x = 0
			# 					last_period = move.invoice_period_id 
			# 				all_dates[move.id] = last_period.date_end - timedelta(days=x)
			# 				x += 1
			# 			else:
			# 				all_dates[move.id] = move.invoice_date_due

			# HEADERS = ['CODIGO DEL DEPOSITANTE', 'NOMBRE DEL DEPOSITANTE', 'INFORMACION DE RETORNO', 'FECHA DE EMISION', 'FECHA DE VENCIMIENTO',\
			# 	'MONTO A PAGAR', 'MORA/CARGO FIJO', 'MONTO MINIMO', 'TIPO DE REGISTRO', 'NRO DOCUMENTO DE PAGO', 'NRO DOCUMENTO DE IDENTIDAD']

			# worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
			# x, c = 1, 0
			# last_due, last_partner = '', ''
			# for line in Moves:
			# 	partner = ''
			# 	if line.partner_id.name:
			# 		partner = line.partner_id.name[:40] if len(line.partner_id.name) > 40 else line.partner_id.name
			# 	concept = '%s SERV %s %d' % (
			# 		line.ref.replace('-', 'N') if line.ref else '',
			# 		months[line.invoice_date_due.month] if line.invoice_date_due else '',
			# 		line.invoice_date_due.year if line.invoice_date_due else 0,
			# 	)
			# 	worksheet.write(x, 0, line.partner_id.ref or '', formats['especial1'])
			# 	worksheet.write(x, 1, self.delete_special_chars(partner), formats['especial1'])
			# 	worksheet.write(x, 2, concept or '', formats['especial1'])
			# 	worksheet.write(x, 3, line.invoice_date or '', formats['reverse_dateformat'])
			# 	worksheet.write(x, 4, all_dates[line.id] or '', formats['reverse_dateformat'])
			# 	worksheet.write(x, 5, line.amount_residual or 0.0, formats['numberdos'])
			# 	worksheet.write(x, 6, 0.0, formats['numberdos'])
			# 	worksheet.write(x, 7, 0.0, formats['numberdos'])
			# 	worksheet.write(x, 8, '', formats['especial1'])
			# 	worksheet.write(x, 9, line.ref.replace('-', 'N') if line.ref else '', formats['especial1'])
			# 	worksheet.write(x, 10, line.partner_id.vat or '', formats['especial1'])
			# 	x += 1

			# widths = [12, 40, 20, 12, 12, 12, 12, 12, 14, 14, 14]
			# worksheet = ReportBase.resize_cells(worksheet, widths)
		elif self.type == 'scotiabank':
			HEADERS = ['CODIGO USUARIO', 'NUMERO RECIBO', 'CODIGO AGRUPACION', 'NOMBRE USUARIO', 'REFERENCIA RECIBO',\
				'CONCEPTO COBRA 1', 'IMPORTE 1', 'CONCEPTO COBRA 2', 'IMPORTE 2', 'CONCEPTO COBRA 3', 'IMPORTE 3', 'CONCEPTO COBRA 4',\
				'IMPORTE 4', 'CONCEPTO COBRA 5', 'IMPORTE 5', 'CONCEPTO COBRA 6', 'IMPORTE 6', 'TOTAL COBRAR', 'PORCENTAJE MINIMO',\
				'ORDEN CRONOLOGICO', 'FECHA EMISION', 'FECHA VENCIMIENTO', 'DIAS PRORROGA', 'INDICADOR DE CARGO AUTOMATICO',\
				'INDICADOR DE TIPO AFILIACION', 'FECHA INICIO CARGO AUTOMATICO', 'FECHA FIN CARGO AUTOMATICO']

			worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
			x = 1
			for line in Moves:
				partner, ref = '', ''
				if line.partner_id.name:
					partner = line.partner_id.name[:20] if len(line.partner_id.name) > 20 else line.partner_id.name
				if line.partner_id.ref:
					ref = line.partner_id.ref[:15] if len(line.partner_id.ref) > 15 else line.partner_id.ref
				worksheet.write(x, 0, ref or '', formats['especial1'])
				worksheet.write(x, 1, line.ref or '', formats['especial1'])
				worksheet.write(x, 2, '', formats['especial1'])
				worksheet.write(x, 3, self.delete_special_chars(partner) or '', formats['especial1'])
				worksheet.write(x, 4, line.invoice_period_id.name or '', formats['especial1'])
				worksheet.write(x, 5, '1', formats['especial1'])
				worksheet.write(x, 6, line.amount_residual or '', formats['numberdos'])
				worksheet.write(x, 7, '', formats['especial1'])
				worksheet.write(x, 8, '', formats['numberdos'])
				worksheet.write(x, 9, '', formats['especial1'])
				worksheet.write(x, 10, '', formats['numberdos'])
				worksheet.write(x, 11, '', formats['especial1'])
				worksheet.write(x, 12, '', formats['numberdos'])
				worksheet.write(x, 13, '', formats['especial1'])
				worksheet.write(x, 14, '', formats['numberdos'])
				worksheet.write(x, 15, '', formats['especial1'])
				worksheet.write(x, 16, '', formats['numberdos'])
				worksheet.write(x, 17, line.amount_residual, formats['numberdos'])
				worksheet.write(x, 18, 0, formats['numberdos'])
				worksheet.write(x, 19, 1, formats['especial1'])
				worksheet.write(x, 20, line.invoice_date or '', formats['reverse_dateformat'])
				worksheet.write(x, 21, line.invoice_date_due or '', formats['reverse_dateformat'])
				worksheet.write(x, 22, '900', formats['especial1'])
				worksheet.write(x, 23, '01', formats['especial1'])
				worksheet.write(x, 24, 'R', formats['especial1'])
				worksheet.write(x, 25, '', formats['reverse_dateformat'])
				worksheet.write(x, 26, '', formats['reverse_dateformat'])
				x += 1

			widths = [14, 14, 12, 40, 20, 12, 14, 12, 14, 12, 14, 12, 14, 12, 14, 12, 14, 14, 14, 12, 14, 14, 12, 12, 12, 14, 14]
			worksheet = ReportBase.resize_cells(worksheet, widths)
		else:
			HEADERS = ['NOMBRES Y APELLIDOS', 'RUC DEL DEPOSITANTE', 'CONCEPTO DE PAGO', 'FECHA VENCIMIENTO', 'FECHA BLOQUEO',\
				'IMPORTE MAX A COBRAR DEUDA', 'IMPORTE MIN A COBRAR DEUDA', 'VALOR SUB CONCEPTO 01', 'VALOR SUB CONCEPTO 02', 'VALOR SUB CONCEPTO 03',\
				'VALOR SUB CONCEPTO 04', 'VALOR SUB CONCEPTO 05', 'VALOR SUB CONCEPTO 06', 'VALOR SUB CONCEPTO 07', 'VALOR SUB CONCEPTO 08',\
				'NUMERO CTA. CLIENTE', 'TIPO IDENTIFICACION', 'NRO IDENTIFICACION',]
			worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
			months = ['', 'ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 'JULIO', 'AGOSTO', 'SETIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
			x = 1
			for line in Moves:
				partner = ''
				if line.partner_id.name:
					partner = line.partner_id.name[:30] if len(line.partner_id.name) > 30 else line.partner_id.name
				concept = 'SERVICIOS %s%d %s' % (
					months[line.invoice_date.month] if line.invoice_date else '',
					line.invoice_date.year if line.invoice_date else 0,
					line.ref,
				)
				worksheet.write(x, 0, self.delete_special_chars(partner) or '', formats['especial1'])
				worksheet.write(x, 1, line.partner_id.ref or '', formats['especial1'])
				worksheet.write(x, 2, concept, formats['especial1'])
				worksheet.write(x, 3, line.invoice_date_due or '', formats['reverse_dateformat'])
				worksheet.write(x, 4, '12/31/2030', formats['reverse_dateformat'])
				worksheet.write(x, 5, line.amount_residual, formats['numberdos'])
				worksheet.write(x, 6, 1, formats['numberdos'])
				worksheet.write(x, 7, '', formats['numberdos'])
				worksheet.write(x, 8, '', formats['numberdos'])
				worksheet.write(x, 9, '', formats['numberdos'])
				worksheet.write(x, 10, '', formats['numberdos'])
				worksheet.write(x, 11, '', formats['numberdos'])
				worksheet.write(x, 12, '', formats['numberdos'])
				worksheet.write(x, 13, '', formats['numberdos'])
				worksheet.write(x, 14, '', formats['numberdos'])
				worksheet.write(x, 15, '', formats['especial1'])
				worksheet.write(x, 16, '', formats['especial1'])
				worksheet.write(x, 17, '', formats['especial1'])
				x += 1

			widths = [40, 14, 20, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14]
			worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()
		f = open(route + doc_name, 'rb')
		file = base64.encodestring(b''.join(f.readlines()))
		self.write({'file': file, 'output_name': doc_name})
		return self.env['popup.it'].get_file(doc_name, file)

class AccountCollectionRecord(models.Model):
	_name = 'account.collection.record'
	_description = 'Account Collection Record'
	
	collection_id = fields.Many2one('account.collection', ondelete='cascade')
	payment_id = fields.Many2one('account.payment', string='Pago')
	move_id = fields.Many2one('account.move', string='Factura')
	partner_id = fields.Many2one('res.partner', related='move_id.partner_id', string='Cliente')
	ref = fields.Char(related='move_id.ref', string='Nro. Documento')
	amount = fields.Float(string='Monto Pagado')
