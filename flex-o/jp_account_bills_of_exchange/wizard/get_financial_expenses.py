# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.tools import float_round

class FinancialExpensesWizard(models.TransientModel):
    _name = "financial.expenses.wizard"
    _description = "Financial Expenses Wizard"

    def _get_amount(self):
        active_id = self.env.context.get('active_id')
        return self.env['account.bill'].search([('id','=',active_id)]).bill_amount_total

    def _get_journal(self):
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if bill_id.origin_bill_id:
            journal_id = bill_id.origin_bill_id.send_form_id.journal_id
        else:
            journal_id = bill_id.send_form_id.journal_id
        return_journal_id = self.env['account.journal'].search([('default_credit_account_id', '=', journal_id.default_credit_account_id.id),('type','=','bank')],limit=1)
        return return_journal_id
        
    def _get_protest_journal(self):
        # Obtener el diario de protestos desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
        return self.env['account.journal'].search([('id','=',protests_boe_journal_id)])

    def _get_currency(self):
        active_id = self.env.context.get('active_id')
        return self.env['account.bill'].search([('id','=',active_id)]).bill_currency_id

    protest_date = fields.Date(string='Protest date', default=fields.Date.context_today)
    different_journal = fields.Boolean(string='Different journal')
    journal_id = fields.Many2one('account.journal', string='Journal for payment', default=_get_journal)
    protest_journal_id = fields.Many2one('account.journal', string='Protest journal', default=_get_protest_journal)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    bill_currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Bill Currency')
    currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Currency')
    # TODO Modificar para que los nombres sean los correctos
    # estan invertidos en todo el modulo, pero funciona
    bank_interests = fields.Monetary(string='Bank Interests', currency_field='currency_id', default=0)
    financial_expenses = fields.Monetary(string='Financial Expenses', currency_field='currency_id', default=0)
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    # gloss = fields.Char('Gloss')
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.bill_currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if self.bill_currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.protest_date)

    @api.onchange('protest_date','journal_id',)
    def onchange_journal(self):
        self.get_rates()
        if not self.journal_id:
            self.different_journal = True
        last_currency_id = self.currency_id
        if self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id
        else:
            self.currency_id = self.env.user.company_id.currency_id
        # if self.currency_id != self.journal_id.currency_id:
        if last_currency_id != self.currency_id:
            self.get_rates()
            if self.company_currency_id != last_currency_id:
                self.bank_interests = float_round(self.bank_interests * self.exchange_rate, 2)
                self.financial_expenses = float_round(self.financial_expenses * self.exchange_rate, 2)
            else:
                self.bank_interests = float_round(self.bank_interests / self.exchange_rate, 2)
                self.financial_expenses = float_round(self.financial_expenses / self.exchange_rate, 2)

    def get_financial_expenses(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Financial Expenses'),
            'res_model': 'financial.expenses.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_financial_expenses_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def send_expenses(self):
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        bill_id.with_context(
            expenses_journal=self.journal_id,
            protest_journal=self.protest_journal_id,
            different_journal=self.different_journal,
            bank_interests=self.bank_interests,
            financial_expenses=self.financial_expenses,
            protest_date=self.protest_date,
            exchange_rate=self.exchange_rate if self.exchange_rate != 0 else 0,
            ).protest_bill()