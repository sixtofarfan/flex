# -*- coding: utf-8 -*-

import datetime
from lxml import etree
from dateutil.relativedelta import relativedelta
import re
import logging
from pytz import timezone
import urllib.request
from bs4 import BeautifulSoup as BS
import calendar
import requests
from odoo import api, fields, models
from odoo.addons.web.controllers.main import xml2json_from_elementtree
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_round
from . import getrate

BANXICO_DATE_FORMAT = '%d/%m/%Y'

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    currency_provider = fields.Selection(selection_add=[('sunat', 'SUNAT Peru')])

    @api.model
    def create(self, vals):
        ''' Change the default provider depending on the company data.'''
        res =  super(ResCompany, self).create(vals)
        if vals.get('country_id') and 'currency_provider' not in vals:
            code_providers = {'PE': 'sunat'}
            cc = self.env['res.country'].browse(vals['country_id']).code.upper()
            if cc in code_providers:
                vals['currency_provider'] = code_providers[cc]
        return res
        
    @api.model
    def set_special_defaults_on_install(self):
        ''' At module isntallation, set the default provider depending on the company country.'''
        res = super(ResCompany, self).set_special_defaults_on_install()
        all_companies = self.env['res.company'].search([])
        for company in all_companies:
            if company.country_id.code == 'PE':
                # Set Superintendencia Nacional de Administracion Tributaria for every peruvian company that was already installed
                company.currency_provider = 'sunat'
        return res

    def get_dictionary(self, from_date, end_date):
        gr = getrate.GetRate(source='SUNAT', date_format='%d/%m/%Y')
        gr.get_exchange_rate('USD', from_date, end_date, self)
        # return dictionary

    def _parse_sunat_data(self, available_currencies):
        ''' Parses the data returned in xml by SUNAT servers and returns it in a more
        Python-usable form.'''

        print('Inicio de tipo de cambio.')
        
        today = datetime.datetime.now()
        tz_name = "America/Lima"
        today_utc = timezone('UTC').localize(today, is_dst=False)
        context_today = today_utc.astimezone(timezone(tz_name))
        date = context_today.strftime("%d/%m/%Y")
        self.get_dictionary(date, date)
        # sell = dictionary.get(date).get('sell',0)
        # buy = dictionary.get(date).get('buy',0)

        # rates_dict = {'USD': (1, context_today), 'PEN': (sell, context_today, buy)}

        # print('Final de tipo de cambio.')

        # return rates_dict

    def _generate_currency_rates(self, parsed_data):
        #Sobreescribimos la funcion para agregar los campos adicionales
        """ Generate the currency rate entries for each of the companies, using the
        result of a parsing function, given as parameter, to get the rates data.

        This function ensures the currency rates of each company are computed,
        based on parsed_data, so that the currency of this company receives rate=1.
        This is done so because a lot of users find it convenient to have the
        exchange rate of their main currency equal to one in Odoo.
        """
        pass
        # Currency = self.env['res.currency']
        # CurrencyRate = self.env['res.currency.rate']

        # today = fields.Date.today()
        # for company in self:
        #     rate_info = parsed_data.get(company.currency_id.name, None)

        #     if not rate_info:
        #         raise UserError(_("Your main currency (%s) is not supported by this exchange rate provider. Please choose another one.") % company.currency_id.name)

        #     base_currency_rate = rate_info[0]
        #     base_buy_rate = rate_info[2] if len(rate_info)>2 else ''

        #     #Agregamos 0 si no tiene el tercer argumento
        #     for item in parsed_data.items():
        #         if len(item[1]) == 2:
        #             parsed_data[item[0]] = item[1]+(0,)

        #     # Verificamos si esta instalado el modulo de ITGRUPO
        #     module_itgrupo = self.env['ir.module.module'].search([('name','=','l10n_pe_currency_rate')])
        #     itgrupo = True if module_itgrupo and module_itgrupo.state == 'installed' else False

            
            # for currency, (rate, date_rate, buy_rate) in parsed_data.items():
            #     rate_value = rate/base_currency_rate

            #     currency_object = Currency.search([('name','=',currency)])
            #     already_existing_rate = CurrencyRate.search([('currency_id', '=', currency_object.id), ('name', '=', date_rate), ('company_id', '=', company.id)])
            #     if already_existing_rate:
            #         already_existing_rate.rate = rate_value
            #         already_existing_rate.sell_rate = base_currency_rate
            #         already_existing_rate.buy_rate = base_buy_rate
            #         # Para ITGRUPO
            #         if itgrupo:
            #             already_existing_rate.sale_type = base_currency_rate
            #             already_existing_rate.purchase_type = base_buy_rate
            #     else:
            #         values = {'currency_id': currency_object.id, 'rate': rate_value, 'name': date_rate, 'company_id': company.id, 'sell_rate': base_currency_rate, 'buy_rate': base_buy_rate}
            #         # Para ITGRUPO
            #         if itgrupo:
            #             values['sale_type'] = base_currency_rate
            #             values['purchase_type'] = base_buy_rate
            #         CurrencyRate.create(values)

    #Funciones para JS
    def update_currency_rates_sunat(self):
        self.env.company.update_currency_rates()
        #test

    def update_currency_rates_range_sunat(self):
        # self.env['res.config.settings'].update_currency_rates_range()
        return {
            'name': _('Update range'),
            'res_model': 'range.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_currency_rate_live.view_range_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def update_currency_rates_range(self):
        
        return {
            'name': _('Update range'),
            'res_model': 'range.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_currency_rate_live.view_range_wizard').id,
            'context': self.env.context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    sell_rate = fields.Float(string='Sell rate', digits=(12, 4))
    buy_rate = fields.Float(string='Buy rate', digits=(12, 4))

    def get_systray_dict(self, date):
        from datetime import datetime
        tz_name = "America/Lima"
        today_utc =  datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        context_today = today_utc.astimezone(timezone(tz_name))
        date = context_today.strftime("%Y-%m-%d")
        # date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        rate = self.env['res.currency.rate'].search([('currency_id', '=', 2),('name','=',date)], limit=1).sorted(lambda x: x.name)
        if rate:
            exchange_rate =  1 / rate.rate
            return {'date': _('Date : ') + rate.name.strftime("%d/%m/%Y"), 'rate': str("{:.4f}".format(exchange_rate)), 'sell': _('Sell: ') + str("{:.4f}".format(rate.sell_rate)), 'buy': _('Buy: ') + str("{:.4f}".format(rate.buy_rate))}
        else:
            return {'date': _('No currency rate for ') + context_today.strftime("%d/%m/%Y"), 'rate': 'N/R', 'sell': _('Sell: ') + '0.0', 'buy': _('Buy: ') + '0.0'}