# -*- coding: utf-8 -*-
from odoo import models, fields, api

# ITGRUPO
# class AccountJournal(models.Model):
#     _inherit = "account.journal"

class ItInvoiceSerie(models.Model):
    _inherit = 'it.invoice.serie'

    # credit_note_id = fields.Many2one(
    #     comodel_name="account.journal", string="Credit Note", domain="[('type','in', ['sale', 'purchase'])]")
    # dedit_note_id = fields.Many2one(
    #     comodel_name="account.journal", string="Debit Note", domain="[('type','in', ['sale', 'purchase'])]")
    credit_note_id = fields.Many2one(comodel_name="einvoice.catalog.01", string="Credit Note")
    dedit_note_id = fields.Many2one(comodel_name="einvoice.catalog.01", string="Debit Note")
    pe_invoice_code = fields.Selection(selection="_get_pe_invoice_code", string="Invoice Type Code")
    pe_payment_method = fields.Selection(selection="_get_pe_payment_method", string="Payment Method")

    @api.model
    def _get_pe_payment_method(self):
        return self.env['pe.datas'].get_selection("PE.TABLA01")

    @api.model
    def _get_pe_invoice_code(self):
        return self.env['pe.datas'].get_selection("PE.TABLA10")
