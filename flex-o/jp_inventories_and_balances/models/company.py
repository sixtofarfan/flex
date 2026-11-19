# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    table_34_sector_id = fields.Many2one('table.34.sector', string=_('PLE Inventories and Balances Sector'))