# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from requests.exceptions import Timeout
import requests
import re
import json

ENDPOINT = 'http://www.sbs.gob.pe/app/stats/seriesH-tipo_cambio_moneda_excel.asp'
CURRENCIES = {
        'USD': '02',
        'CHF': '57',
        'EUR': '66',
        'JPY': '38',
        'MXN': '43',
        'GBP': '34',
        'AUD': '05',
        'BDT': '90',
        'BRL': '10',
        'CAD': '11',
        'COP': '12',
        'GEL': '91',
        'SEK': '55',
    }
def get_months_by_dates(date_start, date_end):
    months_year = []
    date_end = date_end.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)

    while date_start <= date_end:
        months_year.append((date_start.month, date_start.year))
        date_start += relativedelta(months=1)
    
    return months_year

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
    
    def _get_endpoint(self):
        return '{0}?fecha1={1}&fecha2={2}&moneda={3}&cierre='.format(ENDPOINT, (self.from_date - timedelta(days=1)).strftime("%d-%m-%Y"), (self.to_date - timedelta(days=1)).strftime("%d-%m-%Y"), CURRENCIES[self.env.company.foreign_currency_id.name])

    '''YA NO FUNCIONA ESTE CODIGO'''
    # def update_currency_range(self):
    #     max_retries = 5
    #     current_retry = 0
    #     while current_retry < max_retries:
    #         try:
    #             # Desactivar la verificación SSL
    #             requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    #             # Realiza la solicitud al endpoint para obtener el archivo Excel
    #             response = requests.get(self._get_endpoint(), verify=False, timeout=1)
    #             # Verifica si la solicitud fue exitosa (código de estado 200)
    #             if response.status_code == 200:
    #                 table_data = []
    #                 matches = re.findall(r'<TR>(.*?)</TR>', response.text, re.DOTALL)
    #                 if matches:
    #                     matches.pop(0)
    #                 for match in matches:
    #                     cells = re.findall(r'<TD.*?>(.*?)</TD>', match, re.DOTALL)
    #                     table_data.append(cells)

    #                 # Guardar los datos de la tabla en el modelo res_currency
    #                 parse_data = {self.env.company.currency_id.name: (self.env.company.currency_id.rate, self.env.company.currency_id.date)}
    #                 for row in table_data:
    #                     rate_date = datetime.strptime(row[0].strip(), '%d/%m/%Y') + timedelta(days=1)
    #                     parse_data.update({self.env.company.foreign_currency_id.name: (1 / float(row[3]), rate_date.strftime('%Y-%m-%d'))})
    #                     self.env.company.with_context(update_currency_range=True)._generate_currency_rates(parse_data)
    #                     rate_id = self.env.company.foreign_currency_id.rate_ids.filtered(lambda line:line.name == rate_date.date())
    #                     rate_id.write({'purchase_type': float(row[2]), 'sale_type': float(row[3])})
    #                 # Si la solicitud tiene éxito, puedes salir del bucle
    #                 break
    #         except Timeout:
    #             # Si ocurre un Timeout, incrementa el número de intentos y vuelve a intentarlo
    #             current_retry += 1
    #         except Exception as e:
    #             raise UserError(e)
    #     else:
    #         # Este bloque se ejecutará si se agotan los intentos sin éxito
    #         raise UserError(_('The maximum number of attempts (5) has been reached. Please check connection and try again.'))
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'reload',
    #     }

    def update_currency_range(self):
        date = self.from_date
        to_date = self.to_date
        # Validate dates
        self._valid_date(date)
        self._valid_date(to_date)
       
        rate_obj = self.env['res.currency.rate']
        currency = self.env.ref('base.USD')
        # url = 'https://itgrupo.net/api/webservice/currencyraterange'
        url = 'https://api.apis.net.pe/v2/sbs/tipo-cambio'
        date_ini = date - timedelta(days=1)
        date_fin = to_date
        if not self.env.company.token_apis_net:
            raise UserError("Token Apis net, debe ser configurado")
        #test
        # active_currencies = self.env['res.currency'].search([])
        # self.env.company._parse_bcrp_data(active_currencies)
        try:
            months = get_months_by_dates(date_ini,date_fin)
            arre = []
            for month,year in months:
                params = {'token' : self.env.company.token_apis_net,
                        'currency': currency.name,
                        'month': month,
                        'year': year}
                
                r = requests.get(url, params=params)
                rsp =r.json()
                if rsp:
                    arre += rsp
                
            company = self.env.company.parent_id if self.env.company.parent_id else self.env.company

            if currency:
                date_tmp = date_ini
                
                while date_tmp <= date_fin:
                    value = list(filter(lambda l:l.get("fecha") == str(date_tmp - timedelta(days=1)),arre))
                    if not value:
                        i=2
                        while date_tmp >= date_ini  :
                            value = list(filter(lambda l:l.get("fecha") == str(date_tmp - timedelta(days=i)),arre))
                            if value:
                                break
                            i+=1
                        if not value:
                            date_tmp += relativedelta(days=1)
                            continue
                    
                    sale_type = value[0].get("precioVenta",0)
                    purchase_type = value[0].get("precioCompra",0)
                    rate = (sale_type + purchase_type) / 2
                    date_api = str(date_tmp)
                    rate_search = rate_obj.search([
                                ('name', '=', date_api),
                                ('currency_id', '=', currency.id),
                                ('company_id','=',company.id)
                            ],limit=1)

                    if rate_search:
                        rate_search.write({
                            'rate': rate,
                            'sale_type': sale_type,
                            'purchase_type': purchase_type,
                        })
                    else:
                        rate_obj.create({
                            'currency_id': currency.id,
                            'rate': rate,
                            'name': date_api,
                            'sale_type': sale_type,
                            'purchase_type': purchase_type,
                            'company_id': company.id
                        })
                    date_tmp += relativedelta(days=1)
                # for line in arre:
                #     sale_type = line.get("precioVenta",0)
                #     purchase_type = line.get("precioCompra",0)
                #     rate = (sale_type + purchase_type) / 2
                #     date_api = (datetime.strptime(line.get("fecha",""), "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
                #     rate_search = rate_obj.search([
                #                 ('name', '=', date_api),
                #                 ('currency_id', '=', currency.id),
                #                 ('company_id','=',company.id)
                #             ],limit=1)

                #     if rate_search:
                #         rate_search.write({
                #             'rate': rate,
                #             'sale_type': sale_type,
                #             'purchase_type': purchase_type,
                #         })
                #     else:
                #         rate_obj.create({
                #             'currency_id': currency.id,
                #             'rate': rate,
                #             'name': date_api,
                #             'sale_type': sale_type,
                #             'purchase_type': purchase_type,
                #             'company_id': company.id
                #         })
    
        except Exception as err:
            raise UserError(err) 
    
    @staticmethod
    def _valid_date(date):
        # date = datetime.strptime(date, '%d/%m/%Y')
        if date.year < 2000:
            raise UserError('Information available from the 2000 year.')
        return True
    
    '''ESTE CODIGO YA NO FUNCIONA'''
    # def get_sale_purchase_type(self,exch_rate_id,from_date=False,to_date=False):
    #     '''Actualiza el tipo de cambio de venta y compra del dia'''
    #     max_retries = 5
    #     current_retry = 0
    #     while current_retry < max_retries:
    #         try:
    #             # Desactivar la verificación SSL
    #             requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    #             # Realiza la solicitud al endpoint para obtener el archivo Excel
    #             _get_endpoint = '{0}?fecha1={1}&fecha2={2}&moneda={3}&cierre='.format(ENDPOINT, (from_date - timedelta(days=1)).strftime("%d-%m-%Y"), (to_date - timedelta(days=1)).strftime("%d-%m-%Y"), CURRENCIES[self.env.company.foreign_currency_id.name])
    #             response = requests.get(_get_endpoint, verify=False, timeout=1)
    #             # Verifica si la solicitud fue exitosa (código de estado 200)
    #             if response.status_code == 200:
    #                 table_data = []
    #                 matches = re.findall(r'<TR>(.*?)</TR>', response.text, re.DOTALL)
    #                 if matches:
    #                     matches.pop(0)
    #                 for match in matches:
    #                     cells = re.findall(r'<TD.*?>(.*?)</TD>', match, re.DOTALL)
    #                     table_data.append(cells)
    #                 for row in table_data:
    #                     rate_date = datetime.strptime(row[0].strip(), '%d/%m/%Y') + timedelta(days=1)
    #                     # rate_id = self.env.company.foreign_currency_id.rate_ids.filtered(lambda line:line.name == rate_date.date())
    #                     exch_rate_id.write({'purchase_type': float(row[2]), 'sale_type': float(row[3])})
    #                 # Si la solicitud tiene éxito, puedes salir del bucle
    #                 break
    #         except Timeout:
    #             # Si ocurre un Timeout, incrementa el número de intentos y vuelve a intentarlo
    #             current_retry += 1
    #         except Exception as e:
    #             raise UserError(e)
