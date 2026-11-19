# -*- coding: utf-8 -*-

import pytz
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang

class ManualWizard(models.TransientModel):
    _name = 'manual.wizard'
    _description = 'Manual Wizard'

    def _get_rate_value(self):
        return self.env.company.foreign_currency_id.inverse_rate

    manual_rate = fields.Float('Today\'s rate', digits=(12,4), default=_get_rate_value)

    def update_currency_manual(self):
        last_rate = self.env['res.currency.rate'].search([('currency_id', '=', self.env.company.foreign_currency_id.id), ('name','<=',fields.Date.context_today(self))]).sorted(lambda x: x.name)
        if last_rate:
            last_rate[-1].inverse_company_rate = self.manual_rate
        else:
            self.env['res.currency.rate'].create({
                'name': fields.Date.context_today(self),
                'currency_id': self.env.company.foreign_currency_id.id,
                'inverse_company_rate': self.manual_rate
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        