# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class PaymentRequestLine(models.Model):
	_inherit = 'fxo.payment.request.line'
	_order = 'rel_name, rel_partner, amount, rel_date'

	rel_name = fields.Char(related='payment_request_id.name', string='Nro. Solicitud', store=True)
	rel_user = fields.Many2one('res.users', related='payment_request_id.user_request', string='Solicitante', store=True)
	rel_date = fields.Date(related='payment_request_id.date_request', string='Fecha Solicitud', store=True)
	rel_journal = fields.Many2one('account.journal', related='payment_request_id.journal_id', string='Diario de Pago', store=True)
	rel_catalog_payment = fields.Many2one('einvoice.catalog.payment', related='payment_request_id.catalog_payment_id', string='Medio de Pago', store=True)
	rel_bank = fields.Many2one('res.partner.bank', related='payment_request_id.bank_id', string='Cuenta Bancaria', store=True)
	rel_paid_to = fields.Many2one('res.partner', related='payment_request_id.paid_to', string='Girado a', store=True)
	rel_partner = fields.Many2one('res.partner', related='payment_request_id.partner_id', string='Proveedor', store=True)
	amount_residual = fields.Float(string='Monto a Sustentar', compute='get_amount_residual', store=True)
	payment_total = fields.Float(string='Total Pagado')
	payment_residual = fields.Float(string='Total a Pagar', compute='get_payment_residual', store=True)
	notes = fields.Text(related='payment_request_id.supplier_observation', string='Observaciones Proveedor')

	@api.depends('payment_total')
	def get_payment_residual(self):
		for rec in self:
			rec.payment_residual = rec.amount - rec.payment_total

	@api.depends('payment_total', 'amount_invoiced')
	def get_amount_residual(self):
		for rec in self:
			print('get_amount_residual1', rec.payment_total, rec.amount_invoiced)
			rec.amount_residual = rec.payment_total - rec.amount_invoiced

	@api.depends('move_line_ids')
	def get_amount_invoiced(self):
		for rec in self:
			if rec.move_line_ids:
				Lines = rec.move_line_ids.filtered(lambda l: l.move_id.state == 'posted')
				rec.amount_invoiced = sum(Lines.mapped('price_total'))
				self.get_amount_residual()
				print('get_amount_residual2', rec.payment_total, rec.amount_invoiced)
			else:
				rec.amount_invoiced = 0

	def get_request_moves(self):
		#for line in self.env['fxo.payment.request.line'].search([]):
			# MoveLines = self.env['account.move.line'].search([
			# 	('request_line_id', '=', line.id),
			# 	('order_id', '=', line.doc_number.id),
			# 	('product_id', '=', line.product_id.id),
			# 	#('internal_ref_child', '=', line.internal_ref_child),
			# ])
			#line.move_line_ids = [(6, 0, MoveLines.ids)]
		return {
			'name': 'Control de Facturas Canceladas',
			'type': 'ir.actions.act_window',
			'res_model': 'fxo.payment.request.line',
			'views': [
				(self.env.ref('fxo_account_invoice_control.fxo_payment_request_line_view_tree').id, 'tree'),
				(self.env.ref('fxo_account_invoice_control.fxo_payment_request_line_view_form').id, 'form'),
			],
			'search_view_id': self.env.ref('fxo_account_invoice_control.fxo_payment_request_line_view_search').id,
			'context': self._context,
		}

	def get_request_moves_manual(self):
		MoveLines = self.env['account.move.line'].search([
			('request_line_id', '=', self.id),
			('order_id', '=', self.doc_number.id),
			('product_id', '=', self.product_id.id),
		])
		self.move_line_ids = [(6, 0, MoveLines.ids)]

	def get_all_request_data(self):
		Lines = self.env['fxo.payment.request.line'].browse(self._context.get('active_ids'))
		temp = self.env['fxo.payment.request.line.temp'].create({
			'request_line_ids': [(6, 0, Lines.ids)],
			'move_line_ids': [(6, 0, Lines.mapped('move_line_ids').ids)],
		})
		return {
			'name': 'Detalle Completo',
			'type': 'ir.actions.act_window',
			'res_id': temp.id,
			'res_model': 'fxo.payment.request.line.temp',
			'views': [
				(self.env.ref('fxo_account_invoice_control.fxo_payment_request_line_temp_view_form').id, 'form'),
			],
			'context': self._context,
			'target': 'new',
		}


class PaymentRequestLineTemp(models.TransientModel):
	_name = 'fxo.payment.request.line.temp'
	_description = 'Payment Request Line Temp'

	request_line_ids = fields.Many2many('fxo.payment.request.line', 'request_temp_rel')
	move_line_ids = fields.Many2many('account.move.line', 'move_temp_rel')
