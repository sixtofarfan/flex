# -*- coding: utf-8 -*-

import pytz
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang

class ManualWizard(models.TransientModel):
    _name = 'manual.wizard'
    _description = 'Manual Wizard'

    def _get_rate_value(self):
        # already_existing_rate = self.env['res.currency.rate'].search([('currency_id', '=', 2), ('name', '=', fields.Date.context_today(self)), ('company_id', '=', self.env.company.id)])
        # if already_existing_rate:
        #     rate = 1 / already_existing_rate.rate
        # else:
        #     rate = 0
        company = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        return 1/(company.foreign_currency_id.rate or 1)
        

    manual_rate = fields.Float('Today\'s rate', digits=(12,4), default=_get_rate_value)

    def update_currency_manual(self):
        # if self.manual_rate == 0:
        #     raise UserError(_('Currency rate can\'t be zero.'))
        # Currency = self.env['res.currency']
        # CurrencyRate = self.env['res.currency.rate']
        # currency = 'USD'
        # rate_value = self.manual_rate
        # currency_object = Currency.search([('name','=',currency)], limit=1)
        # already_existing_rate = CurrencyRate.search([('currency_id', '=', currency_object.id), ('name', '=', fields.Date.context_today(self)), ('company_id', '=', self.env.company.id)])
        # if already_existing_rate:
        #     already_existing_rate.rate = 1 / rate_value
        #     already_existing_rate.sell_rate = rate_value
        # else:
        #     values = {'currency_id': currency_object.id, 'rate': self.env.company.currency_id.rate / rate_value, 'name': fields.Date.context_today(self), 'company_id': self.env.company.id, 'sell_rate': rate_value,}
        #     CurrencyRate.create(values)
        company = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        last_rate = self.env['res.currency.rate'].search([('currency_id', '=', company.foreign_currency_id.id), ('name','<=',fields.Date.context_today(self))]).sorted(lambda x: x.name)
        last_rate[-1].inverse_company_rate = self.manual_rate
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        