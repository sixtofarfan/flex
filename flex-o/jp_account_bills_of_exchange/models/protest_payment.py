from odoo import models, fields, api, _
# from odoo.exceptions import RedirectWarning, UserError, ValidationError
from datetime import datetime, timedelta, date

class AccountProtestPayment(models.Model):
    _name = 'account.protest.payment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Protest Payment'
    _order = 'payment_date desc'

    name = fields.Char('Protest payment number', copy=False, readonly=True, default=(lambda x: _('New')))
    bill_id = fields.Many2one(comodel_name='account.bill', string='Bill of Exchange')
    # bill_ids = fields.One2many('account.bill', 'bill_form_id', 'Bills of Exchange', tracking=True)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required = True, tracking=True,)
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.company),required=True,string='Company')
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id')
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, string='Currency',default=(lambda self: self.env.user.company_id.currency_id))
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=1)
    payment_amount_total = fields.Monetary(string='Total', currency_field='currency_id', default=0)
    payment_amount_total_signed = fields.Monetary(string='Total Signed', currency_field='company_currency_id', default=0)
    account_move_line_ids = fields.One2many('account.move.line', 'protest_payment_id', string='Account move lines')
    account_move = fields.Many2one('account.move', 'Account Move')
    bill_last_state = fields.Char('Bill Last State')
    last_account_id = fields.Many2one(comodel_name='account.account', string='Bill Last Account')
    type_form = fields.Char(string="Form Type", default='3')

    @api.model
    def create(self, values):
        if not values.get('name', False) or values['name'] == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code('account.protest.payment') or _('New')
        return super(AccountProtestPayment, self).create(values)