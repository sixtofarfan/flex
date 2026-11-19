# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentScotiabank(models.Model):
	_name = 'multiple.payment.scotiabank'
	_description = 'Multiple Payment Scotiabank'

	line_ids = fields.One2many('multiple.payment.scotiabank.line', 'scotiabank_id', states={'txt': [('readonly', True)]})
	charge_currency_id = fields.Many2one('res.currency', string='Moneda', required=True)
	state = fields.Selection([('draft', 'Borrador'),
							  ('txt', 'Txt Generado'),
							  ('payed', 'Pagado')], default='draft')

	def turn_txt(self):
		for record in self:
			record.state = 'txt'

	def turn_draft(self):
		for record in self:
			record.state = 'draft'

	def get_moves(self):
		wizard = self.env['multiple.payment.wizard'].create({'name': 'Facturas'})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'multiple.payment.wizard',
			'views': [[False, 'form']],
			'context': self._context,
			'target': 'new',
		}

	def parse_number_txt(self, number, type, range):
		position = ''.join(range*['0'])
		if type == 'int':
			number = str(number)
			position = position[:-len(number)] + number
		if type == 'float':
			Lang = self.env['res.lang'].search([('active', '=', True)], limit=1)
			number = str(number).split(Lang.decimal_point)
			if len(number[1]) == 1:
				number[1] += '0'
			position = position[:-len(number[0] + number[1])] + number[0] + number[1]
		return position

	def get_scotiabank_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			for line in record.line_ids:
				p_doc_aux2 = ' ' * 11
				bene_aux = ' ' * 60
				doc_aux = ' ' * 18
				email_aux = ' ' * 60
				f.write('{doc_number}{beneficiary_name}{email}{p_doc_num} {charge_currency}{amount}{payment_type}{acc_number}{inter_acc_number}\r\n'.format(
					p_doc_num = line.partner_doc_number + p_doc_aux2[len(line.partner_doc_number):],
					beneficiary_name = line.beneficiary_name + bene_aux[len(line.beneficiary_name):],
					email = line.email + email_aux[len(line.email):] if line.email else email_aux,
					doc_number = line.doc_number + doc_aux[:len(line.doc_number)],
					charge_currency = '0' if record.charge_currency_id.name == 'PEN' else '1',
					amount = self.parse_number_txt(line.amount, 'float', 17),
					payment_type = line.payment_type,
					acc_number = line.payment_acc_number if line.payment_acc_number else ' ' * 14,
					inter_acc_number = line.payment_inter_acc_number if line.payment_inter_acc_number else ' ' * 20,
					))
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentScotiabankLine(models.Model):
	_name = 'multiple.payment.scotiabank.line'
	_description = 'Multiple Payment Scotiabank Line'

	scotiabank_id = fields.Many2one('multiple.payment.scotiabank', ondelete='cascade')
	move_id = fields.Many2one('account.move', string='Factura', required=True)
	partner_doc_number = fields.Char(string='Numero de Documento del Proveedor', size=11, required=True)
	beneficiary_name = fields.Char(string='Nombre del Proveedor', size=60, required=True)
	email = fields.Char(string='Email', size=60)
	doc_number = fields.Char(string='Numero de Documento a Pagar', size=18)
	amount = fields.Float(string='Importe a Abonar', digits=(13, 2), required=True)
	payment_type = fields.Selection([
									(' ', 'Cuenta CCI'),
									('1', 'Cheque de Gerencia'),
									('2', 'Cta. Corriente'),
									('3', 'Cta. Ahorros')], string='Forma de Pago', required=True)
	payment_acc_number = fields.Char(string='Numero de Cuenta de Abono', size=14)
	payment_inter_acc_number = fields.Char(string='Numero de Cuenta Interbancaria', size=20)