# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Table03(models.Model):
    _name = 'table.03'
    _description = 'SUNAT Table 03'
    #TABLA 3: ENTIDAD FINANCIERA

    code = fields.Char(string='Code')
    name = fields.Char(string='Description')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    financial_entity = fields.Many2one('table.03')
    table_03_id = fields.Many2one('table.03', string='SUNAT Table 03')