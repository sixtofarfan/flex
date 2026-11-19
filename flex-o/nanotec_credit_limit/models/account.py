# -*- coding: utf-8 -*-
from odoo import models, fields


class account_payment_term(models.Model):
    _inherit = "account.payment.term"

    _payment_type = (
        ('credit', 'Crédito'),
        ('counted', 'Contado')
        )

    payment_type = fields.Selection(_payment_type, string="Tipo de pago", required=True)
