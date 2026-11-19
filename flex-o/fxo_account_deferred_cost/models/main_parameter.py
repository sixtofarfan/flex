# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	difered_cost_account = fields.Many2one('account.account', string='Cuenta de Gastos Diferidos')
	difered_income_account = fields.Many2one('account.account', string='Cuenta de Ingresos Diferidos')
	difered_tax_journal = fields.Many2one('account.journal', string='Diario para Asiento de Impuesto Diferido')
	difered_cost_journal = fields.Many2one('account.journal', string='Diario de Compras')