# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..models import amount_to_text_es
from datetime import datetime, timedelta, date

class RenewBillForm(models.Model):
    _name = "renew.bill.form"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Renew Bill Form"

    name = fields.Char('Form number', copy=False, readonly=True, default=(lambda x: _('New')))
    renew_date = fields.Date(string='Renew Date', default=fields.Date.context_today, required = True, tracking=True)
    percentage = fields.Float(string='Percentage (%)', tracking=True)
    origin_bill_ids = fields.Many2many('account.bill', string='Bills of Exchange', tracking=True)
    renew_bill_ids = fields.One2many('account.bill', 'renew_form_id', string='Renewals', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, states={'draft': [('readonly', False)]},string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    state = fields.Selection(string='State of form',selection=[('draft', 'Draft'),('created', 'Created'),], default='draft', tracking=True)
    # account_move_line_ids = fields.One2many('account.move.line', 'renew_form_id', string='Account move lines')
    # account_move = fields.Many2one('account.move', 'Account Move')
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1, tracking=True)
    
    def get_exchange_rate(self, amount, currency, company, date):
        return self.currency_id._convert(amount, currency, company, date, False)

    def get_rates(self):
        if not self.custom_exchange_rate:
            if self.currency_id.id == self.company_currency_id.id:
                self.exchange_rate = 1
            else:
                self.exchange_rate = self.get_exchange_rate(1, self.company_id.currency_id, self.company_id, self.renew_date or fields.Date.context_today)

    @api.onchange('currency_id','renew_date','custom_exchange_rate')
    def onchange_currency_id(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            rates = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id),('name','=',self.renew_date or fields.Date.context_today)])
            if not rates:
                raise UserError(_('There is no exchange rate for that date. All the journal entries will be calculated with this rate %s') %self.exchange_rate)
        self.get_rates()

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('renew.bill.form') or _('New')
        return super(RenewBillForm, self).create(values)

    def unlink(self):
        for renew_form in self:
            if renew_form.state != 'draft' and not self._context.get('force_delete'):
                raise UserError(_("You cannot delete a form in %s.") %renew_form.state)
            for bill in renew_form.origin_bill_ids:
                renew_form.origin_bill_ids = [(3, bill.id)]
            for bill in renew_form.renew_bill_ids:
                renew_form.renew_bill_ids = [(3, bill.id)]
        return super(RenewBillForm, self).unlink()

    # def renew_bills_form(self):
    #     '''
    #     :return: Devuelve ir.actions.act_window para mostrar el formulario creado.
    #     '''
    #     active_ids = self.env.context.get('active_ids')
    #     if isinstance(active_ids, list):
    #         bill_ids = self.env['account.bill'].search([('id','in',active_ids)])
    #     else:
    #         a = active_ids[active_ids.find('(')+1:-1].split(',')
    #         bill_ids = self.env['account.bill'].search([('id','in',a)])
    #     if bill_ids:
    #         if any(x.state_of_bill not in ['collection','discount','guarantee','accepted'] for x in bill_ids):
    #             raise UserError(_("You can only renew bills that are in the bank or accepted."))
    #     if bill_ids:
    #         # currency_id = bill_ids[0].bill_currency_id
    #         # if any(x.bill_currency_id != currency_id for x in bill_ids):
    #         #     raise UserError(_("You can only send bills with the same currency."))
    #         # self.currency_id = currency_id
    #         # self.get_rates()
    #         values = {
    #             'renew_date': self.renew_date,
    #             'percentage': self.percentage,
    #             'currency_id': bill_ids[0].bill_currency_id.id,
    #             'exchange_rate': self.exchange_rate,
    #             'origin_bill_ids': [(6, 0, bill_ids.ids)],
    #         }
    #         Renew_Form = self.env['renew.bill.form']
    #         renew_form = Renew_Form.create(values)
    #         action_vals = {
    #             'name': _('New'),
    #             'domain': [('id', '=', renew_form.id),],
    #             'res_model': 'renew.bill.form',
    #             'view_id': self.env.ref('jp_account_bills_of_exchange.view_renew_form').id,
    #             'type': 'ir.actions.act_window',
    #             'res_id': renew_form.id,
    #             'view_mode': 'form',
    #         }
    #         return action_vals

    def create_renew(self):
        if self.state != 'draft':
            raise UserError(_('You can\'t create bills in a form in %s state.' %self.state))
        vals = []
        val = {}
        # active_ids = self.env.context.get('active_ids', [])
        # bills = self.env['account.bill'].search([('id','in',active_ids)])
        if self.origin_bill_ids:
            if any(x.state_of_bill not in ['collection','discount','guarantee', 'disbursed','accepted'] for x in self.origin_bill_ids):
                raise UserError(_("You can only renew bills that are in the bank or accepted."))
        self.get_rates()
        for bill in self.origin_bill_ids:
            bill_date_due = datetime.strptime(str(bill.bill_date_due), '%Y-%m-%d') + timedelta(days=(30))
            # if bill.bill_amount_total == bill.bill_amount_total_signed:
            #     exchange_rate = 1
            # else:
            #     self.exchange_rate = self.get_rates() #self.get_exchange_rate(bill,1, bill.company_currency_id, bill.company_id, fields.Date.context_today)
            if bill.origin_bill_id:
                origin_percentage = round(bill.origin_bill_id.bill_amount_total * (self.percentage / 100), 2)
                if origin_percentage >= bill.bill_amount_total:
                    raise UserError(_('Origin percentage amount %s is greather than or equal to the renewal amount %s. Percentage is calculated based on origin bill amount %s.') %(origin_percentage, bill.bill_amount_total, bill.origin_bill_id.bill_amount_total))
                new_total = bill.bill_amount_total - origin_percentage
            else:
                new_total = round(bill.bill_amount_total * ((100 - self.percentage) / 100), 2)
            new_total_signed = round(new_total * self.exchange_rate, 2)
            a = bill.bill_number
            # renew_number = a + '-1' if a.find('-') == -1 else a[:a.find('-')] + '-' + str(int(a[a.find('-')+1:])+1)
            # NUeva numeración polimaster
            # b=len(a.split('-'))
            # if len(a.split('-')) == 1:
            #     renew_number = a + '-01'
            # elif len(a.split('-')) == 2:
            #     renew_number = a.split('-')[0] + '-' + str(int(a.split('-')[1]) + 1).zfill(2)
            # else:
            #     renew_number = a.split('-')[0] + '-' +a.split('-')[1] + '-' + str(int(a.split('-')[2]) + 1).zfill(2)
            renew_number = a[:-2]+str(int(a[-2:])+1).zfill(2)
            val = {
                'name': renew_number,
                'bank_number': bill.bank_number,
                'renew_form_id': self.id,
                'origin_bill_id':bill.origin_bill_id.id if bill.origin_bill_id else bill.id,
                'renew_bill_id':bill.id,
                'bill_date_due':bill_date_due,
                'bill_date_issue':self.renew_date,
                'bill_number':renew_number,
                'bill_form_id':False,
                'bill_currency_id': bill.bill_currency_id.id,
                'company_id': bill.company_id.id,
                'company_currency_id': bill.company_currency_id.id,
                'guarantee_id':bill.guarantee_id.id,
                'responsable_id':bill.responsable_id.id,
                'acceptor_id':bill.acceptor_id.id,
                'creditor_id':bill.creditor_id.id,
                'bill_amount_total':new_total,
                'bill_amount_total_signed':new_total_signed,
                'exchange_rate':self.exchange_rate,
                'account_id':bill.account_id.id,
                'last_account_id':bill.account_id.id,
                'state_of_bill': 'to_renew',
                'last_state': bill.state_of_bill,
                'type_bill': bill.type_bill,
                'amount_text':amount_to_text_es.amount_to_text(new_total, bill.bill_currency_id.name)
            }
            #new_bill_id = self.env['account.bill'].create(val)
            vals.append(val)
            bill.last_state = bill.state_of_bill
            # bill.state_of_bill = 'to_process'
            # bill.origin_bill_id.write({'renewal_ids': [(4, new_bill_id.id)]})
        self.env['account.bill'].create(vals)
        self.state = 'created'
        for bill in self.origin_bill_ids:
            # bill.last_account_id = bill.account_id
            bill.state_of_bill = 'pending'

    def cancel(self):
        if any(x.state_of_bill not in ['pending'] for x in self.origin_bill_ids):
            raise UserError(_("You can't cancel this form because some bills are in different state."))
        self.state = 'draft'
        for bill in self.origin_bill_ids:
            bill.state_of_bill = bill.last_state
        for bill in self.renew_bill_ids:
            bill.state_of_bill = 'draft'
        self.renew_bill_ids.unlink()