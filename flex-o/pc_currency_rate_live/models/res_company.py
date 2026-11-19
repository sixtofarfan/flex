# -*- coding: utf-8 -*-

import datetime
import logging

import requests

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    foreign_currency_id = fields.Many2one('res.currency', string='Default foreign currency rate')
    json_pe_token = fields.Char('Token json-pe')
    
    def update_currency_rates_sunat(self):
        self.env.company.update_currency_rates()

    #Se ha modificado la funcion original para que guarde los tipos de cambio de venta y compra
    def _generate_currency_rates(self, parsed_data):
        """ Generate the currency rate entries for each of the companies, using the
        result of a parsing function, given as parameter, to get the rates data.

        This function ensures the currency rates of each company are computed,
        based on parsed_data, so that the currency of this company receives rate=1.
        This is done so because a lot of users find it convenient to have the
        exchange rate of their main currency equal to one in Odoo.
        """
        Currency = self.env['res.currency']
        CurrencyRate = self.env['res.currency.rate']

        for company in self:
            rate_info = parsed_data.get(company.currency_id.name, None)

            if not rate_info:
                msg = _("Your main currency (%s) is not supported by this exchange rate provider. Please choose another one.", company.currency_id.name)
                if self._context.get('suppress_errors'):
                    _logger.warning(msg)
                    continue
                else:
                    raise UserError(msg)

            base_currency_rate = rate_info[0]

            for currency, (rate, date_rate) in parsed_data.items():
                rate_value = rate / base_currency_rate

                currency_object = Currency.search([('name', '=', currency)])
                if currency_object:  # if rate provider base currency is not active, it will be present in parsed_data
                    already_existing_rate = CurrencyRate.search([('currency_id', '=', currency_object.id), ('name', '=', date_rate), ('company_id', '=', company.id)])
                    if already_existing_rate:
                        already_existing_rate.rate = rate_value
                    else:
                        obj_curr_rate = CurrencyRate.create({'currency_id': currency_object.id, 'rate': rate_value, 'name': date_rate, 'company_id': company.id})
                    
                    #si update_currency_range es True entonces no debe actualizar el tipo de cambio de venta y compra porque ya 
                    #se hizo de forma manual y por rango
                    if currency_object.name == 'USD':
                        date_rate = datetime.datetime.strptime(str(date_rate), DEFAULT_SERVER_DATE_FORMAT).date()
                        exch_rate_id = already_existing_rate or obj_curr_rate
                        #Invoca a la funcion que actualiza el tipo de cambio de venta y compra
                        active_currencies = self.env['res.currency'].search([])
                        self.update_sale_purchase_currency_rate_daily(exch_rate_id,active_currencies)

    def update_sale_purchase_currency_rate_daily(self,exch_rate_id,available_currencies):
        """Sunat
        Source: https://www.sunat.gob.pe/descarga/TipoCambio.txt
        * The value of the rate is the "official" rate
        * The base currency is always PEN but with the inverse 1/rate.
        """

        result = {}
        available_currency_names = available_currencies.mapped('name')
        if 'PEN' not in available_currency_names or "USD" not in available_currency_names:
            return result
        result['PEN'] = (1.0, fields.Date.context_today(self.with_context(tz='America/Lima')))
        url_format = "https://www.sunat.gob.pe/a/txt/tipoCambio.txt"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            res = requests.get(url_format, headers=headers, timeout=10)
            res.raise_for_status()
            line = res.text.splitlines()[0] or ""
        except Exception as e:
            _logger.error(e)
            return result
        sunat_value = line.split("|")
        try:
            purchase_type = float(sunat_value[1])
            sale_type = float(sunat_value[2])
            exch_rate_id.write(
            {
            'purchase_type': purchase_type,
            'sale_type': sale_type,
            })
        except ValueError as e:
            _logger.error(e)
            return result

    def _parse_bcrp_data(self, available_currencies):
        result = {}
        available_currency_names = available_currencies.mapped('name')
        if 'PEN' not in available_currency_names or "USD" not in available_currency_names:
            return result
        result['PEN'] = (1.0, fields.Date.context_today(self.with_context(tz='America/Lima')))
        url_format = "https://www.sunat.gob.pe/a/txt/tipoCambio.txt"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
        try:
            res = requests.get(url_format, headers=headers, timeout=10)
            res.raise_for_status()
            line = res.text.splitlines()[0] or ""
        except Exception as e:
            _logger.error(e)
            return result
        sunat_value = line.split("|")
        try:
            rate = float(sunat_value[2])
        except ValueError as e:
            _logger.error(e)
            return result
        rate = 1.0 / rate if rate else 0
        date_rate_str = sunat_value[0]
        date_rate = datetime.datetime.strptime(date_rate_str, '%d/%m/%Y').strftime(DEFAULT_SERVER_DATE_FORMAT)
        result["USD"] = (rate, date_rate)
        return result
