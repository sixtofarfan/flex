# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MovePaymentWizard(models.TransientModel):
	_name = 'move.payment.wizard'
	_description = 'Move Payment Wizard'

	request_id = fields.Many2one('fxo.payment.request', string='Solicitud Destino')
	amount_nc = fields.Float(string='Monto MN')
	amount_fc = fields.Float(string='Monto ME')
	currency_rate = fields.Float(string='Tipo Cambio', digits=(12, 4))
	type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')
	number = fields.Char(string='Numero Comprobante')
	account_id = fields.Many2one('account.account', string='Cuenta')
	currency_id = fields.Many2one('res.currency', string='Moneda')
	partner_id = fields.Many2one('res.partner', string='Partner')

	def generate_move(self):
		Request = self.env['fxo.payment.request'].browse(self._context.get('active_id'))
		val = {
			'partner_id': self.partner_id.id,
			'tc': self.currency_rate,
			'type_document_id': self.type_document_id.id,
			'nro_comp': self.number,
			'account_id': self.account_id.id,
			'currency_id': self.currency_id.id,
		}
		line_1 = val.copy()
		line_1.update({
			'matched_request_id': Request.id,
			'name': Request.name,
			'amount_currency': -self.amount_fc if self.currency_id.name == 'USD' else 0,
			'debit': 0,
			'credit': self.amount_nc,
		})
		line_2 = val.copy()
		line_2.update({
			'matched_request_id': self.request_id.id,
			'name': self.request_id.name,
			'amount_currency': self.amount_fc if self.currency_id.name == 'USD' else 0,
			'debit': self.amount_nc,
			'credit': 0,
		})
		return self.env['account.move'].create({
			'partner_id': self.partner_id.id,
			'ref': self.number,
			'type': 'entry',
			'line_ids': [(0, 0, line_1), (0, 0, line_2)],
		})