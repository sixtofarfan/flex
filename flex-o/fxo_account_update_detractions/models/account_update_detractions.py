# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
import base64

class AccountUpdateDetractions(models.Model):
	_name = 'account.update.detractions'
	_description = 'Account Update Detractions'

	date = fields.Date(string='Fecha', default=fields.Date.today())
	output_name = fields.Char(string='Nombre del Archivo')
	file = fields.Binary(string='Archivo de Actualizacion', filename='output_name')
	state = fields.Selection([
		('draft', 'Borrador'),
		('confirmed', 'Confirmado'),
	], string='Estado', default='draft', required=True)

	def update_invoices(self):
		if not self.file:
			raise UserError('Es necesario especificar un archivo de actualizacion')
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
		route = MainParameter.dir_create_file + 'Actualizacion_Detracciones.txt'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.file))
		tmp.close()
		parse_date = ''
		size = len(open(route, encoding='cp1252').readlines())
		with open(route, encoding='cp1252') as f:
			log = ''
			for c, line in enumerate(f, 1):
				if c == 1:
					continue
				elif len(line.split('|')) > 1:
					Partner = self.env['res.partner'].search([('vat', '=', line.split('|')[4])], limit=1)
					if not Partner:
						log += 'No se encontro el partner con el nro documento %s en la linea %d\n' % (line.split('|')[4], c)
						continue
					Catalog = self.env['einvoice.catalog.01'].search([('code', '=', line.split('|')[13])], limit=1)
					if not Catalog:
						log += 'No se encontro el tipo de documento con el codigo %s en la linea %d\n' % (line.split('|')[13], c)
						continue
					serie = line.split('|')[14]
					number = line.split('|')[15]
					ref = serie + '-' + number
					Move = self.env['account.move'].search([
						('ref', '=', ref),
						('type', 'in', ('in_invoice', 'out_invoice')),
						('linked_to_detractions', '=', True),
					], limit=1)
					if not Move:
						log += 'No se encontro el documento %s en la linea %d' % (ref, c)
						continue
					Move.voucher_number = line.split('|')[1]
					Move.date_detraccion = datetime.strptime(line.split('|')[9],'%d/%m/%Y')
			if log:
				return self.env['popup.it'].get_message('Ocurrieron los siguientes errores:\n' + log)
		return self.env['popup.it'].get_message('Se Importo el archivo correctamente')