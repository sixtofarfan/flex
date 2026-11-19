# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Catalog100(models.Model):
    _name = 'catalog.100'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

    
    
