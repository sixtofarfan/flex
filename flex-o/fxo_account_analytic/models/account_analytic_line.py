# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountAnalyticLine(models.Model):
	_inherit = 'account.analytic.line'

	user_id = fields.Many2one('res.users', string='Vendedor')
	sale_team_id = fields.Many2one('crm.team', related='user_id.sale_team_id', string='Equipo de Ventas')
	partner_street_destination = fields.Many2one('res.partner', string='Direccion')
	categ_id = fields.Many2one('product.category', related='product_id.categ_id', string='Categoria de Producto')
	parent_id = fields.Many2one('account.analytic.group', related='account_id.group_id.parent_id', store=True, readonly=True, compute_sudo=True)