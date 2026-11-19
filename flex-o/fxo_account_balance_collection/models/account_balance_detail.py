# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBalanceDetailBook(models.Model):
	_inherit = 'account.balance.detail.book'

	collection = fields.Char(string='Cobrador')
	invoice_period = fields.Char(string='Periodo de Facturacion')