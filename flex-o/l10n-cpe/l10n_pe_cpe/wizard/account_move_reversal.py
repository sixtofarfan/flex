# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    #pe_debit_note_code = fields.Selection(selection="_get_pe_debit_note_type", string="Dedit Note Code")
    # pe_credit_note_code = fields.Selection(
    #     selection="_get_pe_crebit_note_type", string="Credit Note Code")
    pe_credit_note_code = fields.Many2one('einvoice.catalog.09',string='Tipo de Nota de Credito')

    @api.model
    def _get_pe_crebit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

    @api.model
    def _get_pe_debit_note_type(self):
        return self.env['pe.datas'].get_selection("PE.CPE.CATALOG10")

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        serie_id = move.serie_id.credit_note_id.id or res.get('journal_id')
        serie = self.env['it.invoice.serie'].browse(serie_id)
        res.update({
            'journal_id': self.journal_id.id,
            'pe_credit_note_code': self.pe_credit_note_code,
            'pe_invoice_code': serie.pe_invoice_code,
        })
        return res

    def reverse_moves(self):
        res = super(AccountMoveReversal, self).reverse_moves()
        move = self.env['account.move'].search([('id','=', res['res_id'])])
        move.serie_id = self.env['it.invoice.serie'].search([('document_type_id','=',move.type_document_id.code)], limit=1) if move.is_sale_document() else False
        if move.name == '/':
            if move.serie_id:
                next_number = move.serie_id.sequence_id.number_next_actual
                if not move.serie_id.sequence_id.prefix:
                    raise UserError("No existe un prefijo configurado en la secuencia de la serie.")
                prefix = move.serie_id.sequence_id.prefix
                padding = move.serie_id.sequence_id.padding
                move.ref = prefix + "0"*(padding - len(str(next_number))) + str(next_number)
                move.invoice_payment_ref = self.reason
        if self.env.context.get("is_pe_debit_note", False):
            invoice_domain = res['domain']
            if invoice_domain:
                del invoice_domain[0]
                res['domain'] = invoice_domain
            move.debit_note_type_id = self.pe_debit_note_code
            move.pe_debit_note_code = self.pe_debit_note_code
        else:
            move.credit_note_type_id = self.pe_credit_note_code
            move.pe_credit_note_code = self.pe_credit_note_code
        return res
