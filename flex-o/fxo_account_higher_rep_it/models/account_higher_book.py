# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountHigherBook(models.Model):
	_inherit = 'account.higher.book'

	payment_request = fields.Char(string='Solicitud de Pago')
	operation_number = fields.Char(string='Nro. Operacion')
	internal_ref = fields.Char(string='Referencia Interna')
	internal_ref_child = fields.Char(string='Referencia Interna Hija')
	product = fields.Char(string='Producto')
	description = fields.Char(string='Referencia')
	circular = fields.Char(string='Circular')