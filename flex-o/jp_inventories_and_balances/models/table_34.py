# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class Table34(models.Model):
    _name = 'table.34'
    _description = 'SUNAT Table 34'
    #TABLA 34: CÓDIGO DE LOS RUBROS DE LOS ESTADOS FINANCIEROS

    sector_id = fields.Many2one('table.34.sector', string='Sector')
    code = fields.Char(string='Code')
    name = fields.Char(string='Description')
    statement_id = fields.Many2one('table.34.item', string='Financial Statement item')
    # statement_id = fields.Char(string='')
    account_ids = fields.One2many('account.account', 'table_34_id', string='Accounts')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    table_34_id = fields.Many2one('table.34', string='SUNAT Table 34')