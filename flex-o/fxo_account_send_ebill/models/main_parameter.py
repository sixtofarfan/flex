# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MainParameter(models.Model):
    _inherit = 'main.parameter'

    send_email_nf = fields.Boolean(string='Enviar CPE y Correo automaticamente al cliente', default=False)
    send_nubefact = fields.Boolean(string='Enviar por Nubefact', default=False)
    send_multi_credits = fields.Boolean(default=False)
