# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MainParameter(models.Model):
    _inherit = 'main.parameter'

    generate_invoices_for_upgrades = fields.Selection(
        selection=[('service', 'Por cada servicio terminado'), ('day', 'Por día'),
                   ('billing_cycle', 'Por ciclo de facturación')],
        string='Genera Factura (Upgrade Mbps y Renta)', default='billing_cycle')
