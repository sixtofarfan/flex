# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class ResCompany(models.Model):
    _inherit = "res.company"

    det_percent_by = fields.Selection([
        ('1', 'By Product'),
        ('2', 'By Partner'),
        ('3', 'Fixed')
    ], string='Detraction percent method', default='3')