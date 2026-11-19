from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools import float_round

class AccountBankDisbursement(models.Model):
    _name = 'account.bank.disbursement'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Bank Disbursements'
    _order = 'disbursement_date desc'

    name = fields.Char('Bank Disbursement Number', copy=False, readonly=True, default=(lambda x: _('New')))
    send_form_id = fields.Many2one(comodel_name='account.send.bank', string='Send Bills To Bank Form')
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    disbursement_date = fields.Date(string='Disbursement Date', default=False, tracking=True)
    disbursement_amount = fields.Monetary(string='Disbursement Amount', currency_field='currency_id', default=0)
    disbursement_interests = fields.Monetary(string='Bank Interests', currency_field='currency_id', default=0)
    financial_expenses = fields.Monetary(string='Financial Expenses', currency_field='currency_id', default=0)
    journal_id = fields.Many2one('account.journal', string='Journal for Disbursement')
    # disburse_amount_total = fields.Monetary(string='Total', currency_field='currency_id', default=0)
    # disburse_amount_total_signed = fields.Monetary(string='Total Signed', currency_field='company_currency_id', default=0)
    account_move_line_ids = fields.One2many('account.move.line', 'bank_disburse_id', string='Account move lines')
    account_move = fields.Many2one('account.move', 'Account Move')
    is_advanced_payment = fields.Boolean(string='Is advanced payment')
    state = fields.Selection([
        ('payment', 'Advanced payment'),
        ('money', 'Money delivery'),
        ('done', 'Done'),
    ], string='')
    # payment_ids = fields.One2many('account.payment', 'disbursement_id', string='Account payments')
    payment_id = fields.Many2one('account.move', 'Payment move')
    invoice_id = fields.Many2one('account.move', 'Invoice')
    operation_number = fields.Char(string='Operation Number')
    gloss = fields.Char(string='Gloss', required=True)
    interest_gloss = fields.Char(string='Bank Interests operation Number')
    expenses_operation_number = fields.Char(string='Financial Expenses operation Number')

    @api.onchange('gloss')
    def _onchange_gloss(self):
        if self.account_move:
            self.account_move.glosa = self.gloss
            
    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.bank.disbursement') or _('New')
        return super(AccountBankDisbursement, self).create(values)

    # def advance_payment(self):
    #     self.state = 'payment'
    #     val = {}
    #     vals = []
    #     # for partner in self.send_form_id.bill_ids.filtered(lambda bill: bill.is_advanced_payment == True).mapped('responsable_id'):
    #         # total_amount = sum(self.send_form_id.bill_ids.filtered(lambda bill: bill.is_advanced_payment == True and bill.responsable_id == partner).mapped('bill_amount_total'))
    #         # any_bill = self.send_form_id.bill_ids.filtered(lambda bill: bill.is_advanced_payment == True and bill.responsable_id == partner)
    #         #TODO crear el asiento para aplicar en facturas
    #         # first_bill = any_bill[0]
    #         # journal_id = self.env['account.journal'].search([('default_credit_account_id', '=', first_bill.bill_form_id.advanced_bill_form_ids[0].bridge_account_id.id)])
    #         # if not journal_id:
    #         #     raise UserError(_('There is no journal with the brigde account from the bill form of any bill in the default credit account'))
    #     val = {
    #         'name': _('Advanced payment from disbursement %s') %self.name,
    #         'currency_id': self.currency_id.id,
    #         'date': self.disbursement_date,
    #         'invoice_date': self.disbursement_date,
    #         'journal_id': self.journal_id.id,
    #         'glosa': _('Advanced payment %s') %self.name,
    #         'type': 'entry',
    #     }
    #     payment = self.env['account.move'].create(val)
    #     # Linea de desembolso
    #     disbursement_amount_signed = float_round(self.disbursement_amount * self.exchange_rate, 2)
    #     val = {
    #         'ref': self.name,
    #         'partner_id': self.send_form_id.bill_ids.bill_form_id.advanced_bill_form_id.partner_id.id,
    #         'move_id': payment.id,
    #         'exchange_rate': self.exchange_rate,
    #         'name': self.name,
    #         'date': self.disbursement_date,
    #         'journal_id': self.journal_id.id,
    #         'currency_id': self.currency_id.id if self.company_currency_id != self.currency_id else '',
    #         'company_id': self.company_id.id,
    #         'company_currency_id': self.company_currency_id.id,
    #         'account_id': self.journal_id.default_debit_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
    #         'debit': disbursement_amount_signed,
    #         'amount_currency': self.disbursement_amount if self.company_currency_id != self.currency_id else 0,
    #         'tc': self.exchange_rate,
    #         'balance': disbursement_amount_signed, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
    #         'credit':  0,
    #         # 'date_maturity': bill.bill_date_due,
    #     }
    #     vals.append(val)
    #     val = {
    #         'ref': self.name,
    #         'partner_id': self.send_form_id.bill_ids.bill_form_id.advanced_bill_form_id.partner_id.id,
    #         'move_id': payment.id,
    #         'exchange_rate': self.exchange_rate,
    #         'name': self.name,
    #         'date': self.disbursement_date,
    #         'journal_id': self.journal_id.id,
    #         'currency_id': self.currency_id.id if self.company_currency_id != self.currency_id else '',
    #         'company_id': self.company_id.id,
    #         'company_currency_id': self.company_currency_id.id,
    #         'account_id': self.send_form_id.bill_ids.bill_form_id.advanced_bill_form_id.bridge_account_id.id, # if self.invoice_ids[0].type == 'out_invoice' else self.journal_id.default_credit_account_id.id,
    #         'debit': 0,
    #         'amount_currency': self.disbursement_amount * -1 if self.company_currency_id != self.currency_id else 0,
    #         'tc': self.exchange_rate,
    #         'balance': disbursement_amount_signed * -1, # if bill.company_currency_id.id != bill.bill_currency_id.id else 0,
    #         'credit':  disbursement_amount_signed,
    #         # 'date_maturity': bill.bill_date_due,
    #     }
    #     vals.append(val)
    #     self.env['account.move.line'].create(vals)
    #     payment.post()
    #     self.payment_id = payment
    #     lines = payment.line_ids.filtered(lambda line: line.credit > 0)
    #     lines += self.account_move_line_ids.filtered(lambda line: line.account_id == self.send_form_id.bill_ids.bill_form_id.advanced_bill_form_id.bridge_account_id)
    #     lines.reconcile()

    def todos_los_desembosos_con_partner(self):
        all_disbursements = self.env['account.move'].search([('name','ilike','DB-%')])
        for db in all_disbursements:
            for line in db.line_ids:
                if line.bank_disburse_id:
                    db.partner_id = line.bank_disburse_id.journal_id.bank_partner_id
                    if line.account_internal_type == 'liquidity':
                        line.partner_id = line.bank_disburse_id.journal_id.bank_partner_id

    def money_delivery(self):
        self.state = 'money'
        raise UserError(_('This is a money delivery'))

    def cancel(self):
        # for payment in self.payment_ids:
        if any(line.reconciled == True and line.debit > 0 for line in self.payment_id.line_ids):
            raise UserError(_('You can\'t cancel an advanced payment if any payment have been reconciled.'))
        self.payment_id.button_draft()
        self.payment_id.with_context(force_delete=True).unlink()
        self.state = 'advanced'

    # def open_payments_view(self):
    #     [action] = self.env.ref('account.action_account_payments').read()
    #     ids = self.payment_ids.ids
    #     action['domain'] = [('id', 'in', ids)]
    #     return action