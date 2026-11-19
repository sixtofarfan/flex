# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class MainParameter(models.Model):
    _inherit = 'main.parameter'

    adjustment_amount = fields.Float(string='Monto de ajuste', digits=(12, 2))
    adjust_account_id = fields.Many2one('account.account', string='Cuenta de Ajuste Debito')
    adjust_account_credit_id = fields.Many2one('account.account', string='Cuenta de Ajuste Credito')
    custom_journal_id = fields.Many2one('account.journal', string='Diario para Aplicacion de Anticipos por defecto')