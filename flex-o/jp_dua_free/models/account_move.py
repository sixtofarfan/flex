# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_round

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    dua_free = fields.Selection([('dua', 'DUA'),('free', 'Free title'),], string='Change account move lines', copy=False)

    def post(self):
        for invoice in self:
            if invoice.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                # for line in invoice.line_ids:
                if invoice.personalize_tax and invoice.dua_free:
                    purchase_igv_tag = self.env['account.account.tag'].search([('name','=','IGV1')])
                    sale_igv_tag = self.env['account.account.tag'].search([('name','=','IGV-V')])
                    base_tag = self.env['account.account.tag'].search([('name','=','VENTA-G')])
                    if invoice.dua_free == 'dua':
                        # if self.currency_id != self.env.company.currency_id:
                        invoice.line_ids[1].tax_amount_it = invoice.line_ids[1].debit
                        invoice.line_ids[1].tax_amount_me = invoice.line_ids[1].amount_currency
                        invoice.line_ids[1].tag_ids = purchase_igv_tag
                    # TODO hacer el asiento de reversión automatico
                    # else:
                        # total_it = total_me = 0
                        # for line in self.invoice_line_ids:
                        #     line.tax_amount_it = float_round(line.quantity * line.price_unit, 2) * self.currency_rate * -1
                        #     line.tax_amount_me = float_round(line.quantity * line.price_unit, 2) * -1 if self.currency_id != self.env.company.currency_id else 0
                        #     total_it += line.tax_amount_it
                        #     total_me += line.tax_amount_me
                        # line = self.line_ids.filtered(lambda l: l.account_internal_type == 'receivable')
                        # tax = self.env.company.account_sale_tax_id.amount / 100
                        # line.tax_amount_it = total_it * tax
                        # line.tax_amount_me = total_me * tax
                        # line.tag_ids = sale_igv_tag
                        # TODO verificar si hay otro item que no sea gratuito
                        # total_tax_it = total_tax_me = 0
                        # for line in invoice.invoice_line_ids:
                        #     if line.price_subtotal == 0:
                        #         line.tax_amount_it = invoice.invoice_line_ids[0].quantity * invoice.invoice_line_ids[0].price_unit * self.currency_rate
                        #         line.tax_amount_me = (invoice.invoice_line_ids[0].quantity * invoice.invoice_line_ids[0].price_unit) if self.currency_id != self.env.company.currency_id else 0
                        #         line.tag_ids = base_tag
                        #         total_tax_it += line.tax_amount_it
                        #         total_tax_me += line.tax_amount_me
                        # line_tax = invoice.line_ids.filtered(lambda l: sale_igv_tag in l.tag_ids)
                        # for line in invoice.invoice_line_ids:
                        #     for tax in line.tax_ids:
                        #         if tax.amount > 0:
                        #             percentage = tax.amount / 100
                        # if line_tax:
                        #     line_tax.tax_amount_it = line_tax.tax_amount_me = 0
                        #     line_tax.tax_amount_it = total_tax_it * percentage #0.18 #* self.currency_rate
                        #     line_tax.tax_amount_me = (line.tax_amount_me * percentage) if self.currency_id != self.env.company.currency_id else 0
                        # else:
                        #     line_tax.tax_amount_it = line_tax.tax_amount_me = 0
                        #     invoice.line_ids[0].tax_amount_it = total_tax_it * percentage #* self.currency_rate
                        #     invoice.line_ids[0].tax_amount_me = (total_tax_me * percentage) if self.currency_id != self.env.company.currency_id else 0
                        #     invoice.line_ids[0].tag_ids = sale_igv_tag
        return super(AccountMove,self).post()

    @api.depends('amount_total')
    def _get_amount_text(self):
        res = super(AccountMove, self)._get_amount_text()
        for invoice in self:
            if invoice.type in ['out_invoice', 'in_invoice', 'out_refund', 'in_refund']:
                # for line in invoice.line_ids:
                if invoice.personalize_tax and invoice.dua_free:
                    if invoice.dua_free == 'free':
                        amount_text = invoice.currency_id.amount_to_text(0)
                        invoice.amount_text= amount_text
        return res