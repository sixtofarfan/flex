# -*- coding: utf-8 -*-

from odoo import api, fields, models

class IrSequence(models.Model):
    _inherit = "ir.sequence"
    
    is_guide = fields.Boolean(string='Is guide?')