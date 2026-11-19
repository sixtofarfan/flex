# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog04(models.Model):
    _name = 'einvoice.catalog.04'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    descriptio =   fields.Char(string='Descriptio')
    
    
    
