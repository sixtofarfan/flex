# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog03(models.Model):
    _name = 'einvoice.catalog.03'

    name = fields.Char(string='Name')
    desc = fields.Char(string='Descripcion Corta')
    code = fields.Char(string='Code')

    
    
