# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class main_parameter(models.Model):
	_inherit = 'main.parameter'

	a_credit_default= fields.Many2one('account.account','Cuenta Credito Defecto para Cuentas analiticas de Proyectos')
	a_debit_default = fields.Many2one('account.account','Cuenta Debito Defecto para Cuentas analiticas de Proyectos')

	serie_factura = fields.Many2one('it.invoice.serie','Serie para Facturas')
	serie_boleta = fields.Many2one('it.invoice.serie','Serie para Boleta')
	serie_recibo = fields.Many2one('it.invoice.serie','Serie para Recibo')