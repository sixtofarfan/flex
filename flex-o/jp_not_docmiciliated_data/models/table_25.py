# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Table25(models.Model):
    _name = 'table.25'
    _description = 'SUNAT Table 25'
    
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')

    def name_get(self):
        result = []
        for t25 in self:
            result.append((t25.id, t25.code + ' ' + t25.description))
        return result