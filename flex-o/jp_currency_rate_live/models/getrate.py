from datetime import datetime, timedelta
from bs4 import BeautifulSoup as BS
import requests
import pandas as pd
import numpy as np
from pytz import timezone
from .exceptions import InvalidCurrency, InvalidSource, InvalidYearException, NoDataFoundException
from odoo.exceptions import UserError, Warning
from odoo import _
import re
from io import BytesIO
import  json
class GetRate():

    ENDPOINT = 'http://www.sbs.gob.pe/app/stats/seriesH-tipo_cambio_moneda_excel.asp'
    CURRENCIES = {
        'USD': '02',
        'SEK': '55',
        'CHF': '57',
        'CAD': '11',
        'EUR': '66',
        'JPY': '38',
        'GBP': '34'
    }
    date_format = None
    source = None

    def __init__(self, date_format='%d-%m-%Y', source='SBS'):
        self.date_format = date_format
        if source in ['SBS', 'SUNAT']:
            self.source = source
        else:
            raise InvalidSource('The {0} source is invalid.'.format(source))

    def _get_currency(self, currency):
        try:
            return self.CURRENCIES[currency]
        except KeyError:
            raise InvalidCurrency('The {0} currency is invalid.'.format(currency))

    def _get_endpoint(self, currency, from_date, to_date):
        return '{0}?fecha1={1}&fecha2={2}&moneda={3}&cierre='.format(self.ENDPOINT, from_date, to_date, currency)

    def _data_frame(self, currency_code, date, to_date,companies):
        # Valid dates
        self._valid_date(date)
        self._valid_date(to_date)
        # Dates
        date = datetime.strptime(date, '%d/%m/%Y')
        to_date = datetime.strptime(to_date, '%d/%m/%Y')
       
        rate_obj = companies.env['res.currency.rate']
        currency = companies.env.ref('base.USD')
        url = 'https://itgrupo.net/api/webservice/currencyraterange'
        date_ini = date.strftime('%Y/%m/%d')
        date_fin = to_date.strftime('%Y/%m/%d')
        params = {'UserName' : 'APIUserGOLDtc',
                'Password': 'Api$pass&241G13nd4TC',
                'DateIni': date_ini,
                'DateFin': date_fin}
        try:
            r = requests.post(url, params=params)
            arre = r.text.replace("'",'"')
            arr2 = json.loads(arre)
            print("******************* arr2",arr2)
            print("******************* currency",currency)
            print("******************* company",companies)
            if currency:
                for company in companies:
                    for line in arr2:
                        rate_search = rate_obj.search([
                                    ('name', '=', line['name'].replace('/','-')),
                                    ('currency_id', '=', currency.id),
                                    ('company_id','=',company.id)
                                ],limit=1)

                        print("******************* rate_search",rate_search)
                        if rate_search:
                            rate_search.write({
                                'rate': line['rate'],
                                'sale_type': line['sale_type'],
                                'purchase_type': line['purchase_type'],
                            })
                        else:
                            print("******************* else")
                            rate_obj.create({
                                'currency_id': currency.id,
                                'rate': line['rate'],
                                'name': line['name'].replace('/','-'),
                                'sale_type': line['sale_type'],
                                'purchase_type': line['purchase_type'],
                                'company_id': company.id
                            })
    
        except Exception as err:
            raise UserError(err) 

    @staticmethod
    def _convert_source(data_frame):
        idx = []
        for i in data_frame.index:
            i = i + timedelta(days=1)
            idx.append(i.strftime('%d/%m/%Y'))
        return idx

    @staticmethod
    def _to_dict(df):
        data = {}
        for d in df.itertuples():
            d = list(d)
            data[d[0]] = {
                'buy': float('{:.3f}'.format(float(d[2]))),
                'sell': float('{:.3f}'.format(float(d[3])))
            }
        return data

    @staticmethod
    def _valid_date(date):
        date = datetime.strptime(date, '%d/%m/%Y')
        if date.year < 2000:
            raise InvalidYearException(_('Information available from the 2000 year.'))
        return True

    def get_exchange_rate(self, currency, date, to_date=None, env=False):
        currency_code = self._get_currency(currency)
        data_frame = self._data_frame(currency_code, date, to_date or date,env)
        # if data_frame is not None:
        #     data = self._to_dict(data_frame)
        #     if date and not to_date:
        #         date = datetime.strptime(date, '%d/%m/%Y')
        #         return data[date.strftime(self.date_format)]
        #     return data
        # else:
        #     raise NoDataFoundException(_('No data found.'))
