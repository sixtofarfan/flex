# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    apaterno = fields.Char(string='Apellido Paterno')
    amaterno = fields.Char(string='Apellido Materno')
