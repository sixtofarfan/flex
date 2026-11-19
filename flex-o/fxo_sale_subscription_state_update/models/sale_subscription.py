# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleSubscription(models.Model):
	_inherit = 'sale.subscription'

	state_line_ids = fields.One2many('sale.subscription.line.state', 'subscription_id', string='Lineas de Estados')

class SaleSubscriptionLine(models.Model):
	_inherit = 'sale.subscription.line'

	state_line_ids = fields.One2many('sale.subscription.line.state', 'subscription_line_id', string='Lineas de Estados')