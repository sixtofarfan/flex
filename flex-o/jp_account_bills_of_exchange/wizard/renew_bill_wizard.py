# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class RenewBillWizard(models.TransientModel):
    _name = "renew.bill.wizard"
    _description = "Renew Bill Wizard"

    def _get_renew_date(self):
        active_id = self.env.context.get('active_id')
        bill = self.env['account.bill'].search([('id','=',active_id)])
        return bill.bill_date_due

    renew_date = fields.Date(string='Renew Date', default=_get_renew_date, required = True,)
    percentage = fields.Float(string='Percentage (%)', default=10)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)

    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if self.currency_id.id == self.company_currency_id.id:
            self.exchange_rate = 1
        else:
            self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.renew_date or fields.Date.context_today)

    def renew_bills_form(self):
        '''
        :return: Devuelve ir.actions.act_window para mostrar el formulario creado.
        '''
        if self.percentage <10:
            raise UserError(_("Percentage of renewal cannot be lower than 10."))
        active_ids = self.env.context.get('active_ids')
        if isinstance(active_ids, list):
            bill_ids = self.env['account.bill'].search([('id','in',active_ids)])
        else:
            a = active_ids[active_ids.find('(')+1:-1].split(',')
            bill_ids = self.env['account.bill'].search([('id','in',a)])
        if bill_ids:
            if any(x.state_of_bill not in ['collection','discount','guarantee','disbursed','accepted'] for x in bill_ids):
                raise UserError(_("You can only renew bills that are in the bank or accepted."))
        if bill_ids:
            # currency_id = bill_ids[0].bill_currency_id
            # if any(x.bill_currency_id != currency_id for x in bill_ids):
            #     raise UserError(_("You can only send bills with the same currency."))
            # self.currency_id = currency_id
            # self.get_rates()
            self.currency_id = bill_ids[0].bill_currency_id
            self.get_rates()
            values = {
                'renew_date': self.renew_date,
                'percentage': self.percentage,
                'currency_id': bill_ids[0].bill_currency_id.id,
                'exchange_rate': self.exchange_rate,
                'origin_bill_ids': [(6, 0, bill_ids.ids)],
            }
            Renew_Form = self.env['renew.bill.form']
            renew_form = Renew_Form.create(values)
            action_vals = {
                'name': _('New'),
                'domain': [('id', '=', renew_form.id),],
                'res_model': 'renew.bill.form',
                'view_id': self.env.ref('jp_account_bills_of_exchange.view_renew_form').id,
                'type': 'ir.actions.act_window',
                'res_id': renew_form.id,
                'view_mode': 'form',
                'context': {
                    'form_view_initial_mode': 'edit',
                },
            }
            return action_vals