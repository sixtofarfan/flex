# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
import pytz
import urllib.request
import urllib.parse


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def action_sbs_currency(self):
        for obj in self:
            obj._action_sbs_exchange_rate()
        return True

    @api.model
    def _action_sbs_exchange_rate(self):
        url = 'http://www.sbs.gob.pe/app/pp/SISTIP_PORTAL/Paginas/Publicacion/TipoCambioPromedio.aspx'
        try:
            res_html = urllib.request.urlopen(url)
            html = BeautifulSoup(res_html, "lxml")
            tr = html.find("tr", id="ctl00_cphContent_rgTipoCambio_ctl00__0")
            currency = self.env.ref('base.USD')
            if tr and currency:
                tds = tr.findAll("td", {"class": "APLI_fila2"})
                if tds:
                    values = {
                        'compra': float(tds[0].text.strip()),
                        'venta': float(tds[1].text.strip()),
                    }
                    rate_date = fields.Datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz or 'UTC')) + relativedelta(days=1)
                    currency_rate = self.env['res.currency.rate']
                    rate = currency_rate.search([
                        ('currency_id', '=', currency.id),
                        ('name', '=', rate_date.date()),
                    ], limit=1)               
                    if not rate:
                        obj_rate = currency_rate.create({
                            'currency_id': currency.id,
                            'rate': 1.0 / values['venta'],
                            'name': rate_date,
                            'sale_type': values['venta'],
                            'purchase_type': values['compra'],
                        })
                        obj_rate.company_id = False
                    else:
                        rate.write({
                            'rate': 1.0 / values['venta'],
                            'name': rate_date,
                            'sale_type': values['venta'],
                            'purchase_type': values['compra'],
                        })
        except urllib.error.HTTPError as e:
            print('Error: %s' % e)
        except urllib.error.URLError as a:
            print('Error: %s' % a)

class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    _description = "Currency Rate"

    sale_type = fields.Float(
        string='Tipo Venta',
        digits=(12, 3),
    )
    purchase_type = fields.Float(
        string='Tipo Compra',
        digits=(12, 3),
    )
