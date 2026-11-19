# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import *
import base64

class AccountDetractionImport(models.Model):
	_name = 'account.detraction.import'
	_description = 'Account Detraction Import'

	name = fields.Char(string='Referencia', default='/')
	format1 = fields.Binary(string='Archivo Formato Detallado')
	format2 = fields.Binary(string='Archivo Formato Lineal')
	import_date_1 = fields.Datetime(string='Fecha de Importacion')
	file_name_1 = fields.Char(string='Archivo Formato Detallado')
	import_date_2 = fields.Datetime(string='Fecha de Importacion')
	file_name_2 = fields.Char(string='Archivo Formato Lineal')
	import_line_ids = fields.One2many('account.detraction.import.line', 'import_id', domain=[('is_error', '=', True)])
	import_line_registers_ids = fields.One2many('account.detraction.import.line', 'import_id', domain=[('is_error', '=', False)])
	company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id)

	def process_vals(self, vals_list, check_type):
		if check_type:
			self.env['account.detraction.import.line'].search([('format', '=', 'Formato 2')]).unlink()
		else:
			self.env['account.detraction.import.line'].search([('format', '=', 'Formato 1')]).unlink()
		for line in vals_list:
			if check_type:
				type = ['out_invoice'] if line['type'] == 'client' else ['in_invoice']
			else:
				type = ['out_invoice', 'in_invoice']
			move = self.env['account.move'].search([
				('ref', '=', line['ref']),
				('partner_id.vat', '=', line['ruc']),
				('type', 'in', type),
			])
			if move:
				move.voucher_number = line['op_number']
				move.date_detraccion = line['date']
				is_error = False
			else:
				is_error = True
			self.env['account.detraction.import.line'].create({
				'import_id': self.id,
				'partner': line['name'],
				'ruc': line['ruc'],
				'ref': line['ref'],
				'op_number': line['op_number'],
				'date': line['date'],
				'format': line['format'],
				'is_error': is_error,
			})
		if self.name == '/':
			self.name = self.env['ir.sequence'].next_by_code('seq_detraction_import') or '/'
		if not self.import_line_ids:
			return self.env['popup.it'].get_message('Se Importo el archivo correctamente')
		else:
			return self.env['popup.it'].get_message('Hay registros que no se pudieron procesar, revise las lineas de errores')

	def import_format_1(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
		if not self.format1:
			raise UserError('Debe especificar un archivo en el formato 1')
		route = MainParameter.dir_create_file + 'TXT_DETRACCIONES.txt'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.format1))
		tmp.close()
		vals_list = []
		with open(route, encoding="utf-8") as f:
			val = {}
			for line in f:
				if "Fecha y hora de pago" in line:
					date = datetime.strptime(line.split()[5], '%d/%m/%Y').date()
					val['date'] = date
				if "Numero de constancia" in line:
					val['op_number'] = line.split()[3]
				if "Número Documento del Proveedor" in line:
					val['ruc'] = line.split()[4]
				if "Nombre/Razón Social del Proveedor" in line:
					val['name'] = ' '.join(line.split()[4:])
				if "Número de Comprobante" in line:
					val['ref'] = line.split()[3] + '-' + line.split()[4]
					val['format'] = 'Formato 1'
					vals_list.append(val)
					val = {'date': date}
		self.import_date_1 = fields.Datetime.now()
		return self.process_vals(vals_list, False)

	def import_format_2(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
		if not self.format2:
			raise UserError('Debe especificar un archivo en el formato 2')
		route = MainParameter.dir_create_file + 'TXT_DETRACCIONES2.txt'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.format2))
		tmp.close()
		vals_list = []
		with open(route, encoding="latin-1") as f:
			for c, line in enumerate(f):
				val = {}
				if c == 0:
					continue
				splited_line = line.split('|')
				if len(splited_line) == 1:
					raise UserError('El formato del archivo no es correcto, recuerde que el formato 2 es un archivo separado por este character "|"')
				####Client####
				if self.env.company.vat == splited_line[4]:
					val['name'] = splited_line[8]
					val['ruc'] = splited_line[7]
					val['type'] = 'client'
				####Supplier####
				elif self.env.company.vat == splited_line[7]:
					val['name'] = splited_line[5]
					val['ruc'] = splited_line[4]
					val['type'] = 'supplier'
				else:
					raise UserError('El documento tiene lineas que no contienen el ruc de la empresa, RUC: ' + self.env.company.vat)
				val['op_number'] = splited_line[2]
				val['ref'] = splited_line[14] + '-' + splited_line[15]
				val['date'] = datetime.strptime(splited_line[9], '%d/%m/%Y').date()
				val['format'] = 'Formato 2'
				vals_list.append(val)
		self.import_date_2 = fields.Datetime.now()
		return self.process_vals(vals_list, True)

class AccountDetractionImportLine(models.Model):
	_name = 'account.detraction.import.line'
	_description = 'Account Detraction Import Line'

	import_id = fields.Many2one('account.detraction.import', ondelete='cascade')
	partner = fields.Char(string='Nombre del Partner')
	ruc = fields.Char(string='RUC')
	ref = fields.Char(string='Nro. Documento')
	op_number = fields.Char(string='Nro. Operacion')
	date = fields.Date(string='Fecha de Pago')
	format = fields.Char(string='Formato')
	is_error = fields.Boolean()