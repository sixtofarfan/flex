# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date

class DisburseWizard(models.TransientModel):
    _name = "disburse.wizard"
    _description = "Disbursement Wizard"

    def _get_amount(self):
        active_id = self.env.context.get('active_id')
        send_form = self.env['account.send.bank'].search([('id','=',active_id)])
        total_amount = 0
        for bill in send_form.bill_ids:
            total_amount += bill.bill_amount_total
        return total_amount

    def _get_currency(self):
        active_id = self.env.context.get('active_id')
        return self.env['account.send.bank'].search([('id','=',active_id)]).currency_id

    def _get_journal(self):
        active_id = self.env.context.get('active_id')
        send_form_id = self.env['account.send.bank'].search([('id','=',active_id)])
        if send_form_id.journal_id.type == 'bank':
            return send_form_id.journal_id
        
    def _get_default_calim_journal(self):
        # Obtener el diario y las cuentas de reclamos bancarios por default desde la configuración
        params = self.env['ir.config_parameter'].sudo()
        # bank_interests_journal = self.env['account.journal'].search([('id','=',bank_interests_boe_journal_id)])
        bank_claim_journal_id = params.get_param('jp_account_bills_of_exchange.bank_claim_journal_id')
        return self.env['account.journal'].search([('id','=',bank_claim_journal_id)])

    journal_id = fields.Many2one('account.journal', string='Journal for disbursement', default=_get_journal)
    disbursement_date = fields.Date(string='Disbursement Date', default=fields.Date.context_today)
    currency_id = fields.Many2one(string='Currency', comodel_name='res.currency', default=_get_currency)
    disbursement_amount = fields.Monetary(string='Disbursement', currency_field='currency_id', default=_get_amount)
    disbursement_interests = fields.Monetary(string='Bank Interests', currency_field='currency_id')
    financial_expenses = fields.Monetary(string='Financial Expenses', currency_field='currency_id')
    # custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    # exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1,)
    proceed = fields.Boolean(string='Proceed with difference', default = False)
    bank_claim = fields.Boolean(string='Bank claim')
    amount_claim = fields.Float(string='Amount claim', digits=(12, 2))
    bank_claim_journal_id = fields.Many2one('account.journal', string='Claim journal', default=_get_default_calim_journal)
    operation_number = fields.Char(string='Operation Number')
    gloss = fields.Char(string='Gloss', required=True)
    interest_gloss = fields.Char(string='Bank Interests operation Number')
    expenses_operation_number = fields.Char(string='Financial Expenses operation Number')

    # @api.onchange('journal_id','disbursement_date','custom_exchange_rate')
    # def onchange_currency_id(self):
    #     active_id = self.env.context.get('active_id')
    #     send_form = self.env['account.send.bank'].search([('id','=',active_id)])
    #     if not self.custom_exchange_rate:
    #         if self.currency_id != self.env.company.currency_id:
    #             self.exchange_rate = self.currency_id._get_conversion_rate(self.currency_id, self.env.company.currency_id, self.env.company, self.disbursement_date or datetime.datetime.now())
    #         else:
    #             if send_form.currency_id != self.env.company.currency_id:
    #                 self.exchange_rate = self.currency_id._get_conversion_rate(send_form.currency_id, self.env.company.currency_id, self.env.company, self.disbursement_date or datetime.datetime.now())

    @api.onchange('journal_id')
    def onchange_journal(self):
        if not self.journal_id:
            self.different_journal = True
        # last_currency_id = self.currency_id
        if self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id
        else:
            self.currency_id = self.env.company.currency_id
            
    def get_disburse_data(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Disbursement'),
            'res_model': 'disburse.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_disburse_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def disburse(self):
        # Registrar el pago y la fecha
        active_id = self.env.context.get('active_id')
        send_form = self.env['account.send.bank'].search([('id','=',active_id)])
        # Validar los intereses
        interest_rate = send_form.interest_rate / 100
        total_interest = 0
        for bill in send_form.bill_ids:
            # Utilizamos la fecha del desembolso para calcular los intereses
            # ya no la fecha de emision de la factura
            # total_interest += (((interest_rate + 1) ** ((bill.bill_date_due - bill.bill_date_issue).days / 360)) - 1) * bill.bill_amount_total
            total_interest += (((interest_rate + 1) ** ((bill.bill_date_due - self.disbursement_date).days / 360)) - 1) * bill.bill_amount_total
        # if self.currency_id != send_form.currency_id:
        #     if self.currency_id != self.env.company.currency_id:
        #         total_interest = total_interest / self.exchange_rate
        #     else:
        #         total_interest = total_interest * self.exchange_rate
        if abs(round(total_interest,2)) != self.disbursement_interests and not self.proceed:
            # self.env.user.notify_danger(_('The interests at %s%% rate for these bills is %s %s and differs from the Bank Interests amount %s %s entered.') %(str(send_form.interest_rate),self.currency_id.name,str(round(total_interest,2)),self.currency_id.name,str(self.disbursement_interests)))
            raise UserError(_('The interests at %s%% rate for these bills is %s %s and differs from the Bank Interests amount %s %s entered.') %(str(send_form.interest_rate),self.currency_id.name,str(abs(round(total_interest,2))),self.currency_id.name,str(self.disbursement_interests)))
            # warning = _('The interests at %s%% for these bills is %s and differs from the Bank Interests amount %s entered.') %(str(send_form.interest_rate),str(round(total_interest,2)),str(self.disbursement_interests))
            # self.proceed = True
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': _('Warnign'),
            #         'message': warning,
            #         'sticky': False,
            #     }
            # }
        send_form.with_context(
            disbursement_date=self.disbursement_date,
            journal_id=self.journal_id,
            disbursement_amount=self.disbursement_amount,
            disbursement_interests=self.disbursement_interests,
            financial_expenses=self.financial_expenses,
            amount_claim=self.amount_claim,
            bank_claim_journal_id=self.bank_claim_journal_id,
            operation_number=self.operation_number,
            gloss=self.gloss,
            # interest_operation_number=self.interest_operation_number,
            # expenses_operation_number=self.expenses_operation_number,
            ).disburse()

        action_vals = {
            'name': send_form.bank_disbursement_id.name,
            'domain': [('id', '=', send_form.bank_disbursement_id.id)],
            'res_model': 'account.bank.disbursement',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_bank_disbursement_form').id,
            'type': 'ir.actions.act_window',
            'res_id': send_form.bank_disbursement_id.id,
            'view_mode': 'form',
            'context': {
                'form_view_initial_mode': 'readonly',
            },
        }
        return action_vals
            