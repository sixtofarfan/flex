# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
	_inherit = 'account.move'

	apportion_line_ids = fields.One2many('account.move.apportion', 'move_id')

	def get_proration_lines(self):
		for rec in self:
			rec.line_ids.unlink()
			rec.invoice_line_ids.unlink()
			vals = []
			for ap_line in rec.apportion_line_ids:
				if  not ap_line.proration_total or \
					not ap_line.proration_order_id or \
					not ap_line.proration_internal_ref or \
					not ap_line.proration_type or \
					not ap_line.proration_product_id:
					raise UserError('Para actualizar los prorrateos todos los campos de la pestaña Prorrateo deben tener un valor')
				Orders = self.env['sale.order'].search([
					('internal_ref', '=', ap_line.proration_internal_ref),
					('type_id.code', '=', 'R'),
				])
				total_weight = sum(Orders.mapped('total_wieght'))
				total_volume = sum(Orders.mapped('total_volumen'))
				for _ord in Orders:
					if ap_line.proration_type == 'equitable':
						price_unit = ap_line.proration_total / len(Orders)
					else:
						if total_weight > (total_volume/1000):
							price_unit = (ap_line.proration_total / total_weight) * _ord.total_wieght
						else:
							price_unit = (ap_line.proration_total / total_volume) * _ord.total_volumen
					val = (0, 0, {
						'product_id': ap_line.proration_product_id.id,
						'product_uom_id': ap_line.proration_product_id.uom_id.id,
						'price_unit': price_unit,
						'quantity': 1,
						'analytic_account_id': _ord.analytic_account_id.id if _ord.analytic_account_id else None,
						'order_id': _ord.id,
						'currency_id': _ord.pricelist_id.currency_id.id,
						'partner_id': rec.partner_id.id,
						'tax_ids': [(6, 0, ap_line.proration_tax_ids.ids)] if ap_line.proration_tax_ids else None,
					})
					vals.append(val)
			rec.write({'invoice_line_ids': vals})

class AccountMoveApportion(models.Model):
	_name = 'account.move.apportion'
	_description = 'Account Move Apportion'
	
	move_id = fields.Many2one('account.move', ondelete='cascade')
	proration_total = fields.Float(string='Monto Total')
	proration_order_id = fields.Many2one('sale.order', string='Pedido')
	proration_internal_ref = fields.Char(string='Referencia Master', related='proration_order_id.internal_ref')
	proration_type = fields.Selection([
		('wv', 'Peso/Volumen'),
		('equitable', 'Equitativo'),
	], string='Tipo de Prorrateo', default='wv')
	proration_product_id = fields.Many2one('product.product', string='Producto')
	proration_tax_ids = fields.Many2many('account.tax', 'account_move_proration_tax_rel', string='Impuestos')