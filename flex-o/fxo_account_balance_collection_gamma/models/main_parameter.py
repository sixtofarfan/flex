# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MainParameter(models.Model):
    _inherit = 'main.parameter'

    bill_account_ids = fields.Many2many('account.account', 'main_parameter_bill_rel', string='Cuentas para Letras')

