# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountDebitNote(models.TransientModel):
    _inherit = "account.debit.note"

    # pe_debit_note_code = fields.Selection(
    #     selection="_get_pe_debit_note_type", string="Dedit Note Code")
    pe_debit_note_code = fields.Many2one('einvoice.catalog.10',string='Tipo de Nota de Debito')

    # @api.model
    # def _get_pe_debit_note_type(self):
    #     return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

    def _prepare_default_values(self, move):
        res = super()._prepare_default_values(move)
        journal_id = move.journal_id.id or res.get('journal_id')
        journal = self.env['account.journal'].browse(journal_id)
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','08')], limit=1)
        res.update({
            'journal_id': journal.id,
            'ref': '',
            'debit_note_type_id': self.pe_debit_note_code.id,
            'type_document_id': type_document_id.id,
            'glosa': self.reason,
        })
        return res

    # def reverse_moves(self):
    #     res = super(AccountMoveReversal, self).reverse_moves()
    #     if self.env.context.get("is_pe_debit_note", False):
    #         invoice_domain = res['domain']
    #         if invoice_domain:
    #             del invoice_domain[0]
    #             res['domain'] = invoice_domain
    #     return res
