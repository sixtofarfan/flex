# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class FinancialStatementSector(models.Model):
    _name = 'table.34.sector'
    _description = 'Sector de tabla 34'

    code = fields.Char(string='Code')
    name = fields.Char(string='Description')

class FinancialStatementItem(models.Model):
    _name = 'table.34.item'
    _description = 'Item de tabla 34'

    code = fields.Char(string='Code')
    name = fields.Char(string='Description')
