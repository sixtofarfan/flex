# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockLocation(models.Model):
    _inherit = "stock.location"
    
    serie_guia_id = fields.Many2one('ir.sequence', string='Serie de guía')