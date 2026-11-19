# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError, RedirectWarning
from datetime import datetime, timedelta
from pytz import timezone
import requests

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
        json_pe_token = self.env.company.json_pe_token
        foreign_currency_id = self.env.company.foreign_currency_id
        
        if not json_pe_token:
            action = self.env.ref('account.action_account_config')
            raise RedirectWarning(_(
                'There is no token configured on the company from Json-pe.'
                ),
                action.id,
                _('Go to settings'),
            )
            
        initial_date = self.from_date #(fields.Date.today() - fields.Date.today().replace(day=1)).strftime('%Y-%m-%d')
        end_date = self.to_date #fields.Date.today().strftime('%Y-%m-%d')
        
        if end_date and end_date > fields.Date.context_today(self):
            raise UserError(_('You cannot set To date in the future.'))
        
        url = f'https://api.json-pe.com/sunat/tc?fechaInicio={initial_date}&fechaFin={end_date}&apikey={json_pe_token}'

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise UserError(f'Error al conectar con la API: {e}')
            return
        except ValueError:
            raise UserError('Error al procesar la respuesta de la API: Formato JSON no válido')
            return
        
        if 'body' not in data or 'items' not in data['body']:
            raise UserError('Respuesta de API no válida')
        
        for item in data['body']['items']:
            date = fields.Date.from_string(item['fechaSunat'])
            purchase = float(item['compra'])
            sale = float(item['venta'])
            
            existing_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', foreign_currency_id.id),
                ('name', '=', date)
            ])
            
            if existing_rate:
                existing_rate.write({
                    'sale_type': sale,
                    'inverse_company_rate': sale,
                    'purchase_type': purchase,
                })
            else:
                self.env['res.currency.rate'].create({
                    'currency_id': foreign_currency_id.id,
                    'name': date,
                    'sale_type': sale,
                    'inverse_company_rate': sale,
                    'purchase_type': purchase,
                })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
