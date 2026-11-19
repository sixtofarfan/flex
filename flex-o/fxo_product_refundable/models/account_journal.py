# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_liquidation_refundable = fields.Boolean(string='Es reembolso de Liquidacion', default=False, help='Marcar para emitir recibos de liquidacion, la cuenta contable toma del producto')