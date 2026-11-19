from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from datetime import datetime, timedelta, date

class SendToBankWizard(models.TransientModel):
    _name = 'account.send.bank.wizard'
    _description = 'Send Bills to Bank Wizard'

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    journal_id = fields.Many2one('account.journal', string='Bill Journal', required = True,)
    send_date = fields.Date(string='Send Date', default=fields.Date.context_today, required = True,)
    bank_position = fields.Selection(string='Bank Position', selection=[('collection', 'Collection'), ('discount', 'Discount'), ('guarantee', 'Guarantee'),],)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.bank_position = self.journal_id.bank_position

    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if self.currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.send_date or fields.Date.context_today)

    def send_bills_to_bank(self):
        '''
        :return: Devuelve ir.actions.act_window para mostrar el formulario creado.
        '''
        active_ids = self.env.context.get('active_ids')
        if isinstance(active_ids, list):
            bill_ids = self.env['account.bill'].search([('id','in',active_ids)])
        else:
            a = active_ids[active_ids.find('(')+1:-1].split(',')
            if a[len(a)-1] == '':
                a.pop()
            bill_ids = self.env['account.bill'].search([('id','in',a)])
        if bill_ids:
            currency_id = bill_ids[0].bill_currency_id
            if any(x.bill_currency_id != currency_id for x in bill_ids):
                raise UserError(_("You can only send bills with the same currency."))
            if any(x.state_of_bill != 'portfolio' for x in bill_ids):
                raise UserError(_("You can only send bills to the bank in portfolio."))
            currency_id = self.journal_id.currency_id if self.journal_id.currency_id else self.company_currency_id
            if any(x.bill_currency_id != currency_id for x in bill_ids):
                raise UserError(_("You can only send bills in %s to this journal." %(self.journal_id.currency_id.name if self.journal_id.currency_id else self.company_currency_id.name)))
            self.currency_id = currency_id
            self.get_rates()
            values = {
                'journal_id': self.journal_id.id,
                'bank_position': self.bank_position,
                'send_date': self.send_date,
                'currency_id': currency_id.id,
                'exchange_rate': self.exchange_rate,
                'bill_ids': [(6, 0, bill_ids.ids)],
            }
            Send_Form = self.env['account.send.bank']
            send_bank_form = Send_Form.create(values)
            action_vals = {
                'name': _('New'),
                'domain': [('id', '=', send_bank_form.id)],
                'res_model': 'account.send.bank',
                'view_id': self.env.ref('jp_account_bills_of_exchange.view_send_to_bank_form').id,
                'type': 'ir.actions.act_window',
                'res_id': send_bank_form.id,
                'view_mode': 'form',
                'context': {
                    'form_view_initial_mode': 'edit',
                },
            }
            return action_vals
