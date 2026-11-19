# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class Company(models.Model):
    _inherit = "res.company"
    sync_data_server_id = fields.Many2one(comodel_name="sync.data.server", string="Server Sync Data", domain="[('state','=','done')]")
    anonymous_id = fields.Many2one('res.partner', string='Anonymous Partner')
    product_varios_id = fields.Many2one('product.template', string='Producto varios')
    service_varios_id = fields.Many2one('product.template', string='Servicio varios')
