# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	bridge_account_ids = fields.Many2many('account.account', string='Bridge Accounts')