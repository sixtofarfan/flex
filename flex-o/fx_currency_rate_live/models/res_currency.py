# -*- coding: utf-8 -*-e
from pytz import timezone,utc
from odoo import models, api,fields ,_

class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def action_get(self):
        company = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        action_view = self.sudo().env.ref('base.action_currency_form').read()[0]
        action_view['view_mode'] = 'form'
        action_view['views'] = [(False, 'form')]
        action_view['res_id'] = company.foreign_currency_id.id
        return action_view

    @api.model
    def systray_get_currency_rate(self):
        company = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        company.update_currency_rates()
        if company.foreign_currency_id.rate:
            return 1/company.foreign_currency_id.rate
        return company.foreign_currency_id.rate
    
    @api.model
    def systray_get_currency_and_date(self):
        company = self.env.company.parent_id if self.env.company.parent_id else self.env.company
        date = company.foreign_currency_id.date.strftime('%d/%m/%Y') if company.foreign_currency_id.date else ''
        name = company.foreign_currency_id.name or ''
        return _('Date: ') + date + ' ' + name
    
class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"
        
    purchase_type = fields.Float(string='Tipo Compra',digits=(16, 3))
    sale_type = fields.Float(string='Tipo Venta',digits=(16, 3))

    def get_systray_dict(self, date):
        from datetime import datetime
        tz_name = "America/Lima"
        today_utc =  datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        today_utc = today_utc.replace(tzinfo=utc)
        context_today = today_utc.astimezone(timezone(tz_name))
        date = context_today.strftime("%Y-%m-%d")
        # date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        rate = self.env['res.currency.rate'].search([('currency_id', '=', 2),('name','=',date)], limit=1).sorted(lambda x: x.name)
        if rate:
            exchange_rate =  1 / rate.rate
            return {'date': _('Date : ') + rate.name.strftime("%d/%m/%Y"), 'rate': str("{:.4f}".format(exchange_rate)), 'sell': _('Sell: ') + str("{:.4f}".format(rate.sale_type)), 'buy': _('Buy: ') + str("{:.4f}".format(rate.purchase_type))}
        else:
            return {'date': _('No currency rate for ') + context_today.strftime("%d/%m/%Y"), 'rate': 'N/R', 'sell': _('Sell: ') + '0.0', 'buy': _('Buy: ') + '0.0'}