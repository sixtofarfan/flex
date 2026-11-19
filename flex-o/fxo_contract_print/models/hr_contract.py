# -*- encoding: utf-8 -*-
from openerp import fields, models, api
from subprocess import Popen, PIPE


class sale_subscription(models.Model):
    _inherit = 'sale.subscription'

    description_contract = fields.Text("Texto en el contrato", help= "Es el formato del contrato.") 