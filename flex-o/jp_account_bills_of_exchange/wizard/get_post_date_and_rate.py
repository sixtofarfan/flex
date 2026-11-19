# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from odoo.tools import float_round

class ReconcileFormWizard(models.TransientModel):
    _name = "reconcile.form.wizard"
    _description = "Reconcile Form Wizard"

    def _get_exchange_rate(self, amount, currency, company, date):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        bill_form_id = self.env[active_model].search([('id','=',active_id)])
        return bill_form_id.currency_id._convert(amount, currency, company, date, False)

    def _get_rates(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        bill_form_id = self.env[active_model].search([('id','=',active_id)])
        self.exchange_rate = self._get_exchange_rate(1, bill_form_id.company_id.currency_id, bill_form_id.company_id, self.reconcile_date or datetime.now())

    reconcile_date = fields.Date(string='Reconcile date', default=fields.Date.context_today)
    custom_exchange_rate = fields.Boolean(string='Custom Exchange Rate')
    exchange_rate = fields.Float(string='Exchange Rate', digits='Exchange Rate', default=_get_rates)
    
    @api.onchange('reconcile_date')
    def onchange_reconcile_date(self):
        self._get_rates()

    def get_post_date_and_rate(self):
        active_id = self.env.context.get('active_id')
        if not active_id:
            return ''

        return {
            'name': _('Reconcile Form Wizard'),
            'res_model': 'reconcile.form.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_account_bills_of_exchange.view_reconcile_form_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def send_expenses(self):
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        bill_form_id = self.env[active_model].search([('id','=',active_id)])
        bill_form_id.with_context(
            reconcile_date=self.reconcile_date,
            exchange_rate=self.exchange_rate,
            ).reconcile_post_date()