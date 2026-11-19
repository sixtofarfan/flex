# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):
	_inherit = 'account.bank.statement.line'

	order_id = fields.Many2one('sale.order', string='Nro. Operacion')
	internal_ref = fields.Char(related='order_id.internal_ref', string='Referencia Interna')
	type = fields.Char(string='Tipo')