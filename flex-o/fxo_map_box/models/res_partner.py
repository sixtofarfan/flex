# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    longitud = fields.Float(string='longitud')
    latitud = fields.Float(string='latitud')
