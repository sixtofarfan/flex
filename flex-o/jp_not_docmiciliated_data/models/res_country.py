# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResCountry(models.Model):
    _inherit = 'res.country'
    
    table_sunat_35 = fields.Char(string='SUNAT code table 35')