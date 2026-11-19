# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class fxoSaleMainParameter(models.Model):
    _inherit = 'fxo.sale.main.parameter'

    use_tc = fields.Boolean(string='Usar TC para Estudio Económico', default=True)
    tc = fields.Float(string='T.C.', digits=(12, 4))
