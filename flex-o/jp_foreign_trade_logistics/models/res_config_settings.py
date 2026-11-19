# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    kardex_document = fields.Selection([
        ('invoice', 'Invoice'),
        ('guide', 'Guide'),
        ('both', 'Both'),
    ], string='Kardex documents')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        kardex_document = params.get_param('jp_foreign_trade_logistics.kardex_document')
        res.update(
            kardex_document = kardex_document,
        )
        return res

    # @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_foreign_trade_logistics.kardex_document",
            self.kardex_document)