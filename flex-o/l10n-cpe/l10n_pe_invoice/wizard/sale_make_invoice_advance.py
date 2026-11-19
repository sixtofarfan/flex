# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    # @api.multi
    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        order = self.env['sale.order'].browse(
            self._context.get('active_ids', []))
        for invoice_id in order.invoice_ids:
            serie_id = False
            partner_id = invoice_id.partner_id.parent_id or invoice_id.partner_id
            if partner_id.l10n_latam_identification_type_id.code_sunat == "6" and invoice_id.state == 'draft':
                serie = self.env['it.invoice.serie'].search(
                    [('pe_invoice_code', '=', '01')], limit=1)
                serie_id = serie and serie.id or False
            elif invoice_id.state == 'draft':
                serie = self.env['it.invoice.serie'].search(
                    [('pe_invoice_code', '=', '03')], limit=1)
                serie_id = serie and serie.id or False
            if serie_id:
                invoice_id.serie_id = serie_id
            for line in invoice_id.invoice_line_ids:
                line.set_pe_affectation_code()
        return res
