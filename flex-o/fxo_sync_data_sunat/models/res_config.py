# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    anonymous_id = fields.Many2one('res.partner', string='Anonymous Partner', related="company_id.anonymous_id")
    product_varios_id = fields.Many2one('product.template', string='Producto varios', related="company_id.product_varios_id")
    service_varios_id = fields.Many2one('product.template', string='Servicio varios', related="company_id.service_varios_id")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
