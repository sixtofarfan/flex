# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
  
    foreign_currency_id = fields.Many2one('res.currency', string='Default foreign currency rate', related='company_id.foreign_currency_id', readonly=False, required=True)
    json_pe_token = fields.Char(related='company_id.json_pe_token', readonly=False)
