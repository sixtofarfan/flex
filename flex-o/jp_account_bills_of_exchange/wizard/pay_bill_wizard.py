# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

class PayBillWizard(models.TransientModel):
    _name = "pay.bill.wizard"
    _description = "Pay Bill Wizard"

    def _get_payment_date(self):
        active_id = self.env.context.get('active_id')
        bill = self.env['account.bill'].search([('id','=',active_id)])
        return bill.bill_date_due

    def _get_amount(self):
        active_id = self.env.context.get('active_id')
        bill = self.env['account.bill'].search([('id','=',active_id)])
        total_amount = partial_payments = 0
        for pp in bill.partial_payment_ids:
            partial_payments += pp.payment_amount_signed
        total_amount = bill.bill_amount_total - partial_payments
        if self.add_debit_note and bill.protest_debit_note_id.state == 'posted':
            total_amount = bill.bill_amount_total - partial_payments + bill.protest_debit_note_id.amount_residual
        return total_amount

    def _get_journal(self):
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if bill_id.send_form_id:
            if bill_id.origin_bill_id:
                journal_id = bill_id.origin_bill_id.send_form_id.journal_id
            else:
                journal_id = bill_id.send_form_id.journal_id
            return_journal_id = self.env['account.journal'].search([('default_credit_account_id', '=', journal_id.default_credit_account_id.id),('type','=','bank')],limit=1)
            return return_journal_id

    def _get_currency(self):
        active_id = self.env.context.get('active_id')
        return self.env['account.bill'].search([('id','=',active_id)]).bill_currency_id

    payment_date = fields.Date(string='Date', default=_get_payment_date)
    # different_journal = fields.Boolean(string='Different journal')
    sunat_payment_method = fields.Many2one('sunat.payment.method', string='SUNAT payment method')
    journal_id = fields.Many2one('account.journal', string='Journal for payment', default=_get_journal)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    bill_currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Bill Currency')
    currency_id = fields.Many2one(comodel_name='res.currency', default=_get_currency, string='Currency')
    payment_amount = fields.Monetary(string='Amount', currency_field='currency_id', default=_get_amount)
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1,)
    # gloss = fields.Char('Gloss')
    operation_number = fields.Char(string='Operation Number')
    add_debit_note = fields.Boolean(string='Add debit note')
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.bill_currency_id._convert(amount, currency, company, date, False)

    def get_exchange_rate_currency(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if self.bill_currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = round(self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.payment_date),3)

    def get_rates_currency(self):
        if self.currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = round(self.get_exchange_rate_currency(1, self.company_id.currency_id, self.company_id, self.payment_date),3)

    def get_amount_changed(self):
        if self.currency_id != self.bill_currency_id:
            if self.currency_id != self.company_currency_id:
                if not self.custom_exchange_rate:
                    self.get_rates_currency()
                self.payment_amount = round(self._get_amount() / self.exchange_rate, 2)
            else:
                if not self.custom_exchange_rate:
                    self.get_rates()
                self.payment_amount = round(self._get_amount() * self.exchange_rate, 2)
        else:
            self.payment_amount = self._get_amount()

    @api.onchange('journal_id','payment_date','custom_exchange_rate','exchange_rate','add_debit_note')
    def onchange_journal(self):
        if not self.custom_exchange_rate:
            self.get_rates()
        # if not self.journal_id:
        #     self.different_journal = True
        if self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id
        else:
            self.currency_id = self.env.user.company_id.currency_id
        self.get_amount_changed()

    @api.onchange('exchange_rate')
    def onchange_exchange_rate(self):
        if self.custom_exchange_rate:
            self.get_amount_changed()

    def get_payment(self):
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        if not bill_id.protest_debit_note_id or bill_id.protest_debit_note_id.state != 'posted':
            context = "{'debit_note': True}"
        else:
            context = self.env.context
        if not active_id:
            return ''
            
        return {
            'name': _('Pay Bill'),
            'res_model': 'pay.bill.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_pay_bill_wizard').id,
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def pay_bill(self):
        # Registrar el pago y la fecha
        active_id = self.env.context.get('active_id')
        bill_id = self.env['account.bill'].search([('id','=',active_id)])
        # # Validar si el pago es parcial y no es protesto
        # # Si no es protesto se recomienda renovar la letra
        # # con un mensaje de error.
        # if bill_id.bill_currency_id != self.currency_id:
        #     if bill_id.bill_currency_id != self.env.company.currency_id:
        #         currency_payment_amount = self.payment_amount / self.exchange_rate
        #     else:
        #         currency_payment_amount = self.payment_amount * self.exchange_rate
        # else:
        #     currency_payment_amount = self.payment_amount
        # if bill_id.state_of_bill != 'protested' and currency_payment_amount < bill_id.bill_amount_total:
        #     raise UserError(_('This bill can\'t be paid im parts. You can renew this bill'))
        bill_id.payment_date = self.payment_date
        bill_id.payment_amount = self.payment_amount
        bill_id.with_context(active_ids=self.ids, 
            active_model='pay.bill.wizard', 
            active_id=self.id,
            payment_journal=self.journal_id,
            payment_date=self.payment_date,
            payment_currency_id=self.currency_id,
            payment_amount=self.payment_amount,
            exchange_rate=self.exchange_rate if self.exchange_rate != 0 else 0,
            operation_number=self.operation_number,
            add_debit_note= self.add_debit_note,
            ).pay_bill()

    def pay_bill_massive(self):
        # Registrar el pago y la fecha
        active_ids = self.env.context.get('active_ids', [])
        bills = self.env['account.bill'].search([('id','in',active_ids)])
        for bill in bills:
            if bill.state_of_bill in ('paid','to_accept','to_renew','renewed','pending'):
                raise UserError(_('Bill %s in %s state can\'t be paid') %(bill.bill_number,bill.state_of_bill))
            bill.payment_date = self.payment_date
            bill.payment_amount = bill.bill_amount_total
            bill.with_context(active_ids=self.ids, 
                active_model='pay.bill.wizard', 
                active_id=self.id,
                payment_journal=self.journal_id,
                payment_date=self.payment_date,
                payment_currency_id=self.currency_id,
                payment_amount=bill.bill_amount_total,
                exchange_rate=self.exchange_rate,
                operation_number=self.operation_number,
                ).pay_bill()