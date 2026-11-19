# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

class res_company(models.Model):
    _inherit = "res.company"

    term_conditions_text = fields.Text(string='Terminos y condiciones')
    