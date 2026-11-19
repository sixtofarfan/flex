# -*- coding: utf-8 -*-

from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
  
    foreign_currency_id = fields.Many2one('res.currency', string='Default foreign currency rate', related='company_id.foreign_currency_id', readonly=False, required=True)
    token_apis_net = fields.Char("Token APIs Net",related='company_id.token_apis_net',readonly=False)
