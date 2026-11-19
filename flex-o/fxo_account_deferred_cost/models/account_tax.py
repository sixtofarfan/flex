# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountTax(models.Model):
	_inherit = 'account.tax'

	difered_account_id = fields.Many2one('account.account', string='Cuenta de Impuesto Diferido')