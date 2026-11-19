# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
import base64

class AccountCollectionWizard(models.TransientModel):
	_name = 'account.collection.wizard'
	_description = 'Account Collection Wizard'

	collection_file = fields.Binary(string='Archivo Recibido')

	def import_collection_txt(self):
		if not self.collection_file:
			raise UserError('Es necesario especificar un archivo de importacion')
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		Collection = self.env['account.collection'].browse(self._context.get('active_id'))
		Collection.record_ids.unlink()
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
		route = MainParameter.dir_create_file + 'Recaudacion.txt'
		tmp = open(route, 'wb+')
		tmp.write(base64.b64decode(self.collection_file))
		tmp.close()
		parse_date = ''
		size = len(open(route).readlines())
		with open(route) as f:
			log = ''
			for c, line in enumerate(f):
				if c + 1 == size and Collection.type in ['scotiabank', 'bbva']:
					continue
				if c == 0:
					if Collection.type == 'bcp':
						str_date = line[14:22]
					elif Collection.type == 'scotiabank':
						str_date = line[52:60]
					else:
						str_date = line[19:27]
					format_date = '%s/%s/%s' % (str_date[6:], str_date[4:6], str_date[:4])
					parse_date = datetime.strptime(format_date, '%d/%m/%Y').date()
					continue
				if Collection.type == 'bcp':
					serie = line[27:40].split('N')[0]
					number = line[27:40].split('N')[1].strip()
					amount = line[103:118]
					parse_amount = amount[:13] + '.' + amount[13:]
					op_number = line[124:130].strip()
				elif Collection.type == 'scotiabank':
					try:
						serie = line[33:48].strip().split(' ')[0]
						number = line[33:48].strip().split(' ')[1]
					except:
						serie = line[33:48].strip().split('-')[0]
						number = line[33:48].strip().split('-')[1]
					amount = line[72:83]
					parse_amount = amount[:9] + '.' + amount[9:]
					op_number = line[156:169].strip()
				else:
					if len(line[32:80].split('-')) == 3:
						serie = line[32:80].split('-')[1][-4:]
						number = line[32:80].split('-')[2].strip()
					else:
						serie = line[32:80].split('-')[0][-4:]
						number = line[32:80].split('-')[1].strip()
					amount = line[95:110]
					parse_amount = amount[:13] + '.' + amount[13:]
					op_number = line[129:135].strip()
				invoice_range = '0' * 8
				ref = serie + '-' + invoice_range[:-len(number)] + number
				currency = 'USD' if Collection.journal_id.currency_id.name == 'USD' else 'PEN'
				Moves = self.env['account.move'].search([
					('type', '=', 'out_invoice'),
					('invoice_payment_state', '=', 'not_paid'),
					('currency_id.name', '=', currency),
				])
				Invoice = Moves.filtered(lambda i: i.ref == ref)
				if not Invoice or len(Invoice) > 1:
					log += 'No se encontro la factura %s\n' % ref
					continue
				else:
					Invoice = Invoice[0]
					pay = self.env['account.payment'].create({
						'payment_method_id': 1,
						'payment_type': 'inbound',
						'partner_id': Invoice.partner_id.id,
						'partner_type': 'customer',
						'destination_account_id': Invoice.line_ids.filtered(lambda l: l.debit > 0)[0].account_id.id,
						'amount': float(parse_amount),
						'currency_id': Collection.journal_id.currency_id.id if Collection.journal_id.currency_id else self.env.company.currency_id.id,
						'payment_date': parse_date,
						'cash_nro_comp': op_number,
						'catalog_payment_id': self.env['einvoice.catalog.payment'].search([('code', '=', '001')]).id,
						'journal_id': Collection.journal_id.id,
						'type_document_id': Invoice.type_document_id.id,
						'nro_comp': Invoice.ref,
						'communication': Invoice.name,
						'invoice_ids': [(6, 0, [Invoice.id])],
					})
					pay._get_currency_rate()
					self.env['account.collection.record'].create({
						'collection_id': Collection.id,
						'payment_id': pay.id,
						'move_id': Invoice.id,
						'amount': float(parse_amount),
					})
					Collection.write({'date': parse_date, 'file': self.collection_file, 'output_name': 'Archivo de Recaudacion.txt'})
			if log:
				return self.env['popup.it'].get_message('No se lograron importar los siguientes documentos:\n' + log)
		return self.env['popup.it'].get_message('Se Importo el archivo correctamente')