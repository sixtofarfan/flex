# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo import api, fields, models
from odoo.exceptions import UserError

class ApplyPaymentWizard(models.TransientModel):
    _name = 'apply.payment.wizard'
    _description = 'Apply Payment Wizard'
    
    name = fields.Date(string='Fecha Contable', default=fields.Date.today())

    def apply_payment(self):
        payment = self.env['fxo.payment.request'].search([('id','=',self._context['active_id'])])
        entry = payment.create_payment_entry(False,self.name)
        entry.date = self.name
        payment.apply_payments_entry(entry)


class InvoicePaymentWizard(models.TransientModel):
    _name = 'invoice.payment.wizard'
    _description = 'Invoice Payment Wizard'

    journal_id = fields.Many2one('account.journal', string='Diario')
    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')
    line_ids = fields.Many2many('fxo.payment.request.line', 'request_payment_invoice_wizard_rel', domain=lambda self: self._get_line_ids_domain())

    @api.model
    def _get_line_ids_domain(self):
        Request = self.env['fxo.payment.request'].browse(self._context.get('active_id'))
        if Request:
            Lines = Request.line_id.filtered(lambda l: l.amount_invoiced < l.amount)
            return [('id', 'in', Lines.ids)]
        else:
            return []

    def generate_invoices(self):
        Request = self.env['fxo.payment.request'].browse(self._context.get('active_id'))
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        Move = self.env['account.move'].create({
            'partner_id': Request.partner_id.id,
            'type_document_id': self.type_document_id.id,
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'currency_id': Request.line_id[0].currency_id.id,
            'type': 'in_invoice',
            'request_id': Request.id,
            'journal_id': self.journal_id.id,
            'custom_journal_id': MainParameter.custom_journal_id.id if MainParameter.custom_journal_id else None,
            'glosa': '{0}{1}{2}'.format(
                Request.line_id[0].partner_id.name if Request.line_id else '',
                Request.order_id.name if Request.order_id else '',
                Request.line_id[0].product_id.name if Request.line_id else '',
            )
        })
        for line in self.line_ids:
            if line.doc_number.analytic_account_id:
                analytic = line.doc_number.analytic_account_id.id
            elif line.product_id.expense_analytic_account_id:
                analytic = line.product_id.expense_analytic_account_id.id
            else:
                analytic = None
            if self.journal_id.type == 'purchase':
                account = line.product_id.property_account_expense_id
            elif self.journal_id.type == 'sale':
                account = line.product_id.property_account_income_id
            else:
                raise UserError('El diario debe ser de tipo compras o ventas')
            aml_val = {
                'currency_id': line.currency_id.id,
                'account_id': account.id,
                'partner_id': line.partner_id.id,
                'product_id': line.product_id.id,
                'quantity': 1,
                'price_unit': line.amount if line.amount_invoiced == 0 else line.amount - line.amount_invoiced,
                'analytic_account_id': analytic,
                'order_id': line.doc_number.id,
                'request_id': Request.id,
                'request_line_id': line.id,
                'tax_ids': [(6, 0, line.product_id.supplier_taxes_id.ids)] if line.product_id.supplier_taxes_id else None,
            }
            Move.write({
                'invoice_line_ids':[(0, 0, aml_val)]
            })
        currency_rate = Move.currency_id._get_conversion_rate(Move.currency_id, self.env.company.currency_id, self.env.company, Move.date)
        Move._compute_invoice_taxes_by_group()
        Move._compute_amount()
        Move.currency_rate = currency_rate
        Move.get_refundable_journal()
        Request.invoice_ids = [(4, Move.id)]