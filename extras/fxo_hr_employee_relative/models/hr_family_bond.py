# -*- encoding: utf-8 -*-
from odoo import fields, models, api
from datetime import *


class HrFamilyBond(models.Model):
    _name = 'hr.family.bond'
    _description = 'Hr Family Bond'

    name = fields.Char(string='Nombre')
    description = fields.Char(string='Descripcion')
    code = fields.Char(string='Codigo')
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id.id)
