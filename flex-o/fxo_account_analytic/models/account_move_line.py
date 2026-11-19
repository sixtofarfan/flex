# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	user_id = fields.Many2one('res.users', string='Vendedor')
	sale_team_id = fields.Many2one('crm.team', related='user_id.sale_team_id', string='Equipo de Ventas')
	partner_street_destination = fields.Many2one('res.partner', string='Direccion')
	categ_id = fields.Many2one('product.category', related='product_id.categ_id', string='Categoria de Producto')