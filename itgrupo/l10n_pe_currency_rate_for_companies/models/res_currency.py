# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_compare
import pytz
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class ResCurrency(models.Model):
	_inherit = "res.currency"
	
	@api.model
	def _action_sunat_exchange_rate(self):
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
					rate_date = fields.Datetime.now().replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
					currency_rate = self.env['res.currency.rate']
					for cmpny in self.env['res.company'].search([]):
						rate = currency_rate.search([
							('currency_id', '=', currency.id),
							('name', '=', rate_date.date()),
							('company_id','=',cmpny.id)
						], limit=1)
						if not rate:
							currency_rate.create({
								'currency_id': currency.id,
								'rate': 1.0 / values['venta'],
								'name': rate_date,
								'sale_type': values['venta'],
								'purchase_type': values['compra'],
								'company_id': cmpny.id,
							})
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
			
	#######################