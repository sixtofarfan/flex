# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class PosConfig(models.Model):
    _inherit = 'pos.config'

    anonymous_id = fields.Many2one('res.partner', string='Anonymous Partner')
    # iface_journals = fields.Boolean(
    #     "Show Sale Journals", help="Enables the use of journals from the Point of Sale")
    iface_series = fields.Boolean(
        "Show Sale Series", help="Enables the use of series from the Point of Sale")
    # invoice_journal_ids = fields.Many2many(
    #     "account.journal", string="Invoice Sale Journals", domain="[('type', 'in', ['sale'])]")
    invoice_serie_ids = fields.Many2many('it.invoice.serie', string='It Invoice Serie')
    is_sync = fields.Boolean("Synchronous")
