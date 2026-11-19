# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMove(models.Model):
    """docstring for AccountMove"""
    _inherit = "account.move"

    rate_pe = fields.Char(string='Tipo de Cambio $', readonly=True)

    @api.onchange('partner_id', 'currency_id')
    def _get_exchange_rate(self):
        if self.currency_id.name == "USD":
            rate_obj = self.env['res.currency'].search([('name', '=', 'USD')])
            self.rate_pe = rate_obj.rate_pe
