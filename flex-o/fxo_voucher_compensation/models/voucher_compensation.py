# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round

class VoucherCompensation(models.Model):
    _name = 'voucher.compensation'
    _description = 'Voucher Compensation'

    name = fields.Char(string='Name', copy=False, readonly=True, default=(lambda x: _('New')))
    journal_id = fields.Many2one('account.journal', string='Compensation Journal')
    partner_id = fields.Many2one('res.partner', string='Customer / Vendor')
    compensation_date = fields.Date(string='Compensation Date', default=fields.Date.today())
    invoice_ids = fields.Many2many('account.move', 'invoice_compensation_id', string='Customer Invoices')
    bill_ids = fields.Many2many('account.move', 'bill_compensation_id', string='Customer Invoices')
    invoice_amount = fields.Float(string='Invoices amount', digits=(12, 2))
    bill_amount = fields.Float(string='Bills amount', digits=(12, 2))
    company_id = fields.Many2one(comodel_name='res.company', default=(lambda self: self.env.company), required=True, string='Company', compute='_compute_company_id', store=True)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', string='Foreign Currency')
    custom_rate = fields.Boolean(string='Custom rate', default=False)
    currency_rate = fields.Float(string='Currency Rate', digits=(12, 4))
    compensation_move = fields.Many2one('account.move', string='Compensation Move')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', string='State')

    def _compute_company_id(self):
        for compensation in self:
            compensation.company_id = compensation.journal_id.company_id or compensation.company_id or self.env.company

    @api.onchange('invoice_ids','bill_ids','currency_rate')
    def _onchange_invoice_bill_ids(self):
        # Sumamos los comprobantes y las rectificativas
        # Moneda nacional
        vouchers = sum(self.invoice_ids.filtered(lambda m: m.type == 'out_invoice' and m.currency_id == self.company_currency_id).mapped('amount_residual_signed')) # sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and (not l.currency_id or l.currency_id == self.company_currency_id)).mapped('amount_residual'))
        # print(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and (not l.currency_id or l.currency_id == self.company_currency_id)))
        refund_vouchers = abs(sum(self.invoice_ids.filtered(lambda m: m.type == 'in_refund' and m.currency_id == self.company_currency_id).mapped('amount_residual_signed'))) # abs(sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and (not l.currency_id or l.currency_id == self.company_currency_id)).mapped('amount_residual')))
        invoice_amount_signed = vouchers + refund_vouchers # sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and (not l.currency_id or l.currency_id == self.env.company.currency_id)).mapped('amount_residual'))
        # Moneda extranjera
        vouchers = sum(self.invoice_ids.filtered(lambda m: m.type == 'out_invoice' and m.currency_id != self.company_currency_id).mapped('amount_residual')) # sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and l.currency_id != self.company_currency_id).mapped('amount_residual_currency'))
        refund_vouchers = abs(sum(self.invoice_ids.filtered(lambda m: m.type == 'in_refund' and m.currency_id != self.company_currency_id).mapped('amount_residual'))) # abs(sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and l.currency_id != self.company_currency_id).mapped('amount_residual_currency')))
        invoice_amount_currency = vouchers + refund_vouchers # sum(self.invoice_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and l.currency_id != self.env.company.currency_id).mapped('amount_residual_currency'))
        # Total
        self.invoice_amount = invoice_amount_signed + invoice_amount_currency * self.currency_rate
        # Lo mismo para las facturas
        # Moneda nacional
        vouchers = abs(sum(self.bill_ids.filtered(lambda m: m.type == 'in_invoice' and m.currency_id == self.company_currency_id).mapped('amount_residual_signed'))) # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and (not l.currency_id or l.currency_id == self.company_currency_id)).mapped('amount_residual')))
        refund_vouchers = abs(sum(self.bill_ids.filtered(lambda m: m.type == 'out_refund' and m.currency_id == self.company_currency_id).mapped('amount_residual_signed'))) # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and (not l.currency_id or l.currency_id == self.company_currency_id)).mapped('amount_residual')))
        bill_amount_signed = vouchers + refund_vouchers # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and (not l.currency_id or l.currency_id == self.env.company.currency_id)).mapped('amount_residual')))
        # Moneda extranjera
        vouchers = abs(sum(self.bill_ids.filtered(lambda m: m.type == 'in_invoice' and m.currency_id != self.company_currency_id).mapped('amount_residual'))) # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and l.currency_id != self.company_currency_id).mapped('amount_residual_currency')))
        refund_vouchers = abs(sum(self.bill_ids.filtered(lambda m: m.type == 'out_refund' and m.currency_id != self.company_currency_id).mapped('amount_residual'))) # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'receivable' and l.currency_id != self.company_currency_id).mapped('amount_residual_currency')))
        bill_amount_currency = vouchers + refund_vouchers # abs(sum(self.bill_ids.line_ids.filtered(lambda l: l.account_internal_type == 'payable' and l.currency_id != self.env.company.currency_id).mapped('amount_residual_currency')))
        # Total
        self.bill_amount = bill_amount_signed + bill_amount_currency * self.currency_rate

    @api.onchange('compensation_date','currency_id')
    def _onchange_compensation_date(self):
        currency_rate = self.env['res.currency.rate'].search([('name','=',self.compensation_date),('currency_id','=',self.currency_id.id),('company_id','=',self.company_id.id)],limit=1)
        self.currency_rate = currency_rate.sell_rate if currency_rate else 0

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('voucher.compensation') or _('New')
        return super(VoucherCompensation, self).create(values)

    def compensate_vouchers(self):
        vals = []
        total_credit = total_debit = 0
        if self.invoice_amount > self.bill_amount:
            total_max = self.bill_amount
        else:
            total_max = self.invoice_amount

        self.compensation_move = self.env['account.move'].create({
            'name': '/',
            'journal_id': self.journal_id.id,
            'date': self.compensation_date,
            'glosa': _('Voucher Compensation %s') %self.name,
            'type': 'entry',
            'currency_rate': self.currency_rate,
        })
        # Buscamos las cuentas puente de parametros principales para no duplicar lineas
        # y evitar error con los asientos de apertura
        main_parameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        bridge_accounts = main_parameter.bridge_account_ids
        for invoice in self.invoice_ids:
            total_credit_currency = 0
            account = invoice.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).account_id
            if invoice.currency_id == self.company_currency_id:
                total_credit_signed = sum(invoice.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual'))
                total_credit = total_credit_signed
            else:
                if self.currency_rate == 0 and invoice.currency_id != self.company_currency_id:
                    raise UserError(_('Currency rate is 0'))
                total_credit_currency = sum(invoice.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual_currency'))
                total_credit = float_round(total_credit_currency * self.currency_rate, 2)
            if sum(val['credit'] for val in vals) + total_credit  > total_max:
                total_credit = total_max - sum(val['credit'] for val in vals) 
                if total_credit < 0:
                    total_credit = 0
                if invoice.currency_id != self.company_currency_id and total_credit > 0:
                    total_credit_currency = total_credit / self.currency_rate
            if total_credit > 0:
                val = {
                    'move_id': self.compensation_move.id,
                    'partner_id': self.partner_id.id,
                    'type_document_id': invoice.type_document_id.id,
                    'nro_comp': invoice.ref,
                    'account_id': account.id,
                    'currency_id': invoice.currency_id.id if invoice.currency_id != self.company_currency_id else '',
                    'amount_currency': total_credit_currency * -1 if total_credit_currency else 0,
                    'balance': total_credit * -1,
                    'debit': 0,
                    'credit': total_credit,
                    'tc': self.currency_rate,
                }
                vals.append(val)
        for bill in self.bill_ids:
            account = bill.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).account_id
            total_debit_currency = 0
            if bill.currency_id == self.company_currency_id:
                total_debit_sigend = abs(sum(bill.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual')))
                total_debit = total_debit_sigend
            else:
                total_debit_currency = abs(sum(bill.line_ids.filtered(lambda l: l.account_internal_type in ('payable','receivable') and l.account_id not in bridge_accounts).mapped('amount_residual_currency')))
                total_debit = float_round(total_debit_currency * self.currency_rate, 2)
            if sum(val['debit'] for val in vals) + total_debit  > total_max:
                total_debit = total_max - sum(val['debit'] for val in vals) 
                if total_debit < 0:
                    total_debit = 0
                if bill.currency_id != self.company_currency_id and total_debit > 0:
                    total_debit_currency = total_debit / self.currency_rate
            if total_debit > 0:
                val = {
                    'move_id': self.compensation_move.id,
                    'partner_id': self.partner_id.id,
                    'type_document_id': bill.type_document_id.id,
                    'nro_comp': bill.ref,
                    'account_id': account.id,
                    'currency_id': bill.currency_id.id if bill.currency_id != self.company_currency_id else '',
                    'amount_currency': total_debit_currency if total_debit_currency else 0,
                    'balance': total_debit,
                    'debit': total_debit,
                    'credit': 0,
                    'tc': self.currency_rate,
                }
                vals.append(val)
        self.env['account.move.line'].create(vals)
        self.compensation_move.post()
        for line in self.compensation_move.line_ids.filtered(lambda l: l.credit > 0):
            for debit_line in self.invoice_ids.line_ids.filtered(lambda l: not l.reconciled and l.amount_residual != 0 and l.account_id not in bridge_accounts):
                reconcile_lines = debit_line
                if reconcile_lines and not line.reconciled:
                    reconcile_lines += line
                    reconcile_lines.reconcile()
        for line in self.compensation_move.line_ids.filtered(lambda l: l.debit > 0):
            for credit_line in self.bill_ids.line_ids.filtered(lambda l: not l.reconciled and l.amount_residual != 0 and l.account_id not in bridge_accounts):
                reconcile_lines = credit_line
                if reconcile_lines and not line.reconciled:
                    reconcile_lines += line
                    reconcile_lines.reconcile()
        self.state = 'done'
    
    def cancel(self):
        self.compensation_move.button_draft()
        self.compensation_move.with_context(force_delete=True).unlink()
        self.state = 'draft'