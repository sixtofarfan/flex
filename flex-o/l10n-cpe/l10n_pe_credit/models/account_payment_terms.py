# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    undefined = fields.Boolean(string='Undefined fees')