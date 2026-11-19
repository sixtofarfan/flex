# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class PaymentRequestWizard(models.TransientModel):
	_name = 'fxo.payment.request.wizard'

	name = fields.Char()
	journal_id = fields.Many2one('account.journal', string='Diario', domain="[('type', 'in', ['bank', 'cash'])]")
	catalog_payment_id = fields.Many2one('einvoice.catalog.payment', string='Medio de Pago')
	cash_nro_comp = fields.Char(string='Nro. de Op. Caja')
	payment_date = fields.Date(string='Fecha de Pago', default=fields.Date.context_today)
	manual_batch_payment_id = fields.Many2one('account.batch.payment', string='Lote de Pago')
	cash_flow_id = fields.Many2one('account.cash.flow', string='Flujo de Caja')
	type_doc_cash_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento de Caja')
	communication = fields.Char(string='Circular')

	def create_payments(self):
		for record in self.env['fxo.payment.request'].browse(self._context.get('active_ids')):
			Payments = []
			if record.state == 'done':
				for line in record.line_id:
					Payment = self.env['account.payment'].create({
						'payment_method_id': 2,
						'payment_type': 'outbound',
						'partner_id': line.partner_id.id,
						'partner_type': 'supplier',
						'amount': line.amount,
						'currency_id': line.currency_id.id,
						'payment_date': self.payment_date,
						'journal_id': self.journal_id.id,
						'catalog_payment_id': self.catalog_payment_id.id,
						'cash_nro_comp': self.cash_nro_comp,
						'manual_batch_payment_id': self.manual_batch_payment_id.id or None,
						'cash_flow_id': self.cash_flow_id.id or None,
						'type_doc_cash_id': self.type_doc_cash_id.id or None,
						'communication': self.communication or '',
						'order_id': line.doc_number.id or None,
					})
					Payments.append(Payment.id)
			record.payment_ids = [(6, 0, Payments)]