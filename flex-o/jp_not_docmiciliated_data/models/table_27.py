# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Table27(models.Model):
    _name = 'table.27'
    _description = 'SUNAT Table 27'
    
    code = fields.Char(string='Code')
    description = fields.Char(string='Description')
    type_relation = fields.Char(string='Type of economic relationship according to the Regulations of the Income Tax Law - S.D. N ° 122-94-EF and amendments')
    
    def name_get(self):
        result = []
        for t27 in self:
            result.append((t27.id,t27.code + ' ' + t27.description))
        return result