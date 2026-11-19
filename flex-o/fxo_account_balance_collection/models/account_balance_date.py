# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBalanceDateBook(models.Model):
	_inherit = 'account.balance.date.book'

	collection = fields.Char(string='Cobrador')
	invoice_period = fields.Char(string='Periodo de Facturacion')