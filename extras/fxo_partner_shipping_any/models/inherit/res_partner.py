from odoo import models, fields, api
from odoo.exceptions import ValidationError, Warning
import re


class InheritResPartner(models.Model):
    _inherit = ["res.partner"]

    partner_shipping_id = fields.Many2one('res.partner', string='Direccion de Entrega')