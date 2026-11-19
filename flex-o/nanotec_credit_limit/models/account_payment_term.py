# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
from itertools import chain

from odoo.tools import safe_eval

class account_payment_term(models.Model):
    _inherit = "account.payment.term"

    is_credit_control = fields.Boolean("Control crédito", help="Se controla el crédito en las ordenes de venta?")