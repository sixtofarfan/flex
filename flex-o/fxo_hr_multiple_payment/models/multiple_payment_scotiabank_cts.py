# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentScotiabankCTS(models.Model):
	_name = 'multiple.payment.scotiabank.cts'
	_description = 'Multiple Payment Scotiabank CTS'

	line_ids = fields.One2many('multiple.payment.scotiabank.cts.line', 'scotiabank_cts_id', states={'txt': [('readonly', True)]})
	charge_currency_id = fields.Many2one('res.currency', string='Moneda', required=True)
	register_type = fields.Selection([
									('DU', 'Urgencia'),
									('NO', 'Normal'),
									], string='Tipo de Abono', default='NO')
	company_code = fields.Char(string='Codigo de Empresa', size=10)
	total_charge = fields.Float(compute='_get_total_charge', string='Importe a Cargar', required=True, digits=(13, 2))
	state = fields.Selection([('draft', 'Borrador'),
							  ('txt', 'Txt Generado'),
							  ('payed', 'Pagado')], default='draft')

	@api.depends('line_ids')
	def _get_total_charge(self):
		for record in self:
			record.total_charge = sum(record.line_ids.mapped('amount')) if record.line_ids else 0

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

	def get_scotiabank_cts_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			company_code_aux = ' ' * 10
			f.write('0{register_type}{company_code}{currency}{total}\r\n'.format(
					register_type = record.register_type if record.register_type else ' ' * 2,
					company_code = record.company_code + company_code_aux[len(record.company_code):] if record.company_code else ' ',
					currency = '92' if record.charge_currency_id.name == 'PEN' else '01',
					total = self.parse_number_txt(record.total_charge, 'float', 15),
				))
			for line in record.line_ids:
				p_doc_aux2 = ' ' * 11
				bene_aux = ' ' * 60
				doc_aux = ' ' * 18
				email_aux = ' ' * 60
				f.write('1{currency}{cts_account}{charge_currency}{amount}{cci_account}{rem_currency}{rem_amount}\r\n'.format(
					currency = '92' if record.charge_currency_id.name == 'PEN' else '01',
					cts_account = line.payment_acc_number,
					charge_currency = '92' if record.charge_currency_id.name == 'PEN' else '01',
					amount = self.parse_number_txt(line.amount, 'float', 15),
					cci_account = line.cci_acc_number if line.cci_acc_number else ' ' * 20,
					rem_currency = '92' if record.charge_currency_id.name == 'PEN' else '01',
					rem_amount = self.parse_number_txt(line.rem_amount, 'float', 15),
					))
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank CTS.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentScotiabankCTSLine(models.Model):
	_name = 'multiple.payment.scotiabank.cts.line'
	_description = 'Multiple Payment Scotiabank CTS Line'

	scotiabank_cts_id = fields.Many2one('multiple.payment.scotiabank.cts', ondelete='cascade')
	move_id = fields.Many2one('hr.cts.line', string='CTS', required=True)
	payment_acc_number = fields.Char(string='Numero de Cuenta de Abono', size=14)
	amount = fields.Float(string='Importe a Abonar', digits=(13, 2), required=True)
	cci_acc_number = fields.Char(string='Numero de Cuenta Interbancaria', size=20)
	rem_amount = fields.Float(string='Importe de Remuneracion', digits=(13,2))