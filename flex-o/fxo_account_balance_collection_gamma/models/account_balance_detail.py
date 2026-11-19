# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBalanceDetailBook(models.Model):
	_inherit = 'account.balance.detail.book'
	
	user_request = fields.Char(string='Solicitante')
	moneda = fields.Char(string='Moneda')
	payment_request = fields.Char(string='Solicitud de Pago')
	operation_number = fields.Char(string='Nro. Operacion')
	internal_ref = fields.Char(string='Referencia Interna')
	internal_ref_child = fields.Char(string='Referencia Interna Hija')
	product = fields.Char(string='Producto')