# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

class RenewDateWizard(models.TransientModel):
    _name = "renew.date.wizard"
    _description = "Renew Date Wizard"

    # def _get_amount(self):
    #     active_id = self.env.context.get('active_id')
    #     from_amount = self.env['account.bill'].search([('id','=',active_id)]).renew_bill_id.bill_amount_total
    #     renewal_amount = self.env['account.bill'].search([('id','=',active_id)]).bill_amount_total
    #     to_pay = from_amount - renewal_amount
    #     return to_pay

    def _get_journal(self):
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if bill_id.origin_bill_id:
            journal_id = bill_id.origin_bill_id.send_form_id.journal_id
        else:
            journal_id = bill_id.send_form_id.journal_id
        return_journal_id = self.env['account.journal'].search([('default_credit_account_id', '=', journal_id.default_credit_account_id.id),('type','=','bank')],limit=1)
        return return_journal_id

    def _get_currency(self):
        active_id = self.env.context.get('active_id')
        return self.env['account.bill'].search([('id','=',active_id)]).bill_currency_id

    def _get_type_bill(self):
        active_id = self.env.context.get('active_id')        
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if bill_id.type_bill == 'payable':
            return True
        else:
            return True

    renew_date = fields.Date(string='Renew date', default=fields.Date.context_today)
    different_journal = fields.Boolean(string='Different journal', default=_get_type_bill)
    journal_id = fields.Many2one('account.journal', string='Journal for renew', default=_get_journal)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    bill_currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Bill Currency')
    currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Currency')
    financial_expenses = fields.Monetary(string='Financial Expenses', currency_field='currency_id', default=0)
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.bill_currency_id._convert(amount, currency, company, date, False)

    def get_exchange_rate_currency(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if self.bill_currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.renew_date)

    def get_rates_currency(self):
        if self.currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = self.get_exchange_rate_currency(1, self.company_id.currency_id, self.company_id, self.renew_date)

    @api.onchange('journal_id','renew_date')
    def onchange_journal(self):
        self.get_rates()
        if self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id
        else:
            self.currency_id = self.env.user.company_id.currency_id
        if self.currency_id != self.bill_currency_id:
            if self.currency_id != self.company_currency_id:
                self.get_rates_currency()
                self.financial_expenses = round(self.financial_expenses / self.exchange_rate, 2)
            else:
                self.get_rates()
                self.financial_expenses = round(self.financial_expenses * self.exchange_rate, 2)

    def get_date(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Renew Date'),
            'res_model': 'renew.date.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_renew_date_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def define_date(self):
        # active_ids = self.env.context.get('active_ids')
        active_ids = self.env.context.get('active_ids')
        bills = self.env['account.bill'].search([('id','in',active_ids)])
        if any(bill.state_of_bill != 'to_renew' for bill in bills):
            raise UserError(_('You can only apply renewals to bills in state To Renew.'))
        for bill in bills:
            bill.renew_date = self.renew_date
            bill.with_context(
                renew_journal_id=self.journal_id,
                renew_financial_expenses=self.financial_expenses,
                ).renew_bill()