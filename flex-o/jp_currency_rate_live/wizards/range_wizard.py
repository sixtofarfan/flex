# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from pytz import timezone

class RangeWizard(models.TransientModel):
    _name = 'range.wizard'
    _description = 'Range Wizard'

    def get_time_zone(self):
        today = datetime.now()
        tz_name = "America/Lima"
        today_utc = timezone('UTC').localize(today, is_dst=False)
        context_date = today_utc.astimezone(timezone(tz_name))
        return context_date

    def _first_day(self):
        today_local = self.get_time_zone()
        first_day = today_local - timedelta(days=today_local.day - 1)
        return first_day.strftime("%Y-%m-%d")

    def _last_day(self):
        last_day = self.get_time_zone()
        return last_day.strftime("%Y-%m-%d")

    from_date = fields.Date(string='From date', default=_first_day)
    to_date = fields.Date(string='To date', default=_last_day)

    def update_currency_range(self):
        if self.from_date > self.to_date:
            raise UserError(_('From date cannot be greather than to date.'))
        context_from = self.get_time_zone()
        from_date = self.from_date.strftime("%d/%m/%Y")
        to_date = self.to_date.strftime("%d/%m/%Y")
        self.env.company.get_dictionary(from_date, to_date)
        # while self.from_date <= self.to_date:
        #     context_from = self.from_date
        #     if context_from.strftime("%d/%m/%Y") in dictionary:
        #         sell = dictionary.get(context_from.strftime("%d/%m/%Y")).get('sell',0)
        #         buy = dictionary.get(context_from.strftime("%d/%m/%Y")).get('buy',0)
        #         rates_dict = {'USD': (1, context_from), 'PEN': (sell, context_from, buy)}
        #         self.env.company._generate_currency_rates(rates_dict)
        #     self.from_date += timedelta(days=1)