from odoo import api, fields, models, _
import json
import requests

from odoo.exceptions import UserError, ValidationError

class BillForm(models.Model):
	_inherit = 'account.advanced.bill.form'

	method_registro = fields.Char(string='Metodo de Registro',default="Odoo")
	id_loges = fields.Char(string='Id Loges')

	def process(self):
		url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
		status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')

		super(BillForm,self).process()
		if status_api == "True":
			if self.method_registro == "Odoo" :
				headers = {'Content-type': 'application/json'}
				datos = {
							"company_belonging":  self.company_id.id,
							"bill_number": self.name,
							"registration_date": str(self.create_date),
							"type_document_client": self.partner_id.l10n_latam_identification_type_id.code_sunat,
							"number_document_client": self.partner_id.vat,
							"total_capital": self.advanced_amount,
							"date_emission": str(self.create_date),
							"journal_id": self.journal_id.code,
							"date_request": str(self.create_date),
							"bill_form_id": self.name,
							"id_odoo": self.id
						}
				url_requests = str(url_api) + 'api/1.0/synchronization/from.odoo/advance_letter/'
				r = requests.post(url_requests, data =json.dumps(datos) , headers=headers)
				try:
					validate = r.json()
					
					if validate['status_code'] != 201:
						raise UserError(r.text )
				except Exception as err:
					raise UserError(r.text )
				if validate['status_code'] == 201:
					print(validate)
					self.id_loges = validate['data']['id_loges']
					for item in self.bill_ids:
						line  = {
									"company_belonging": self.company_id.id,
									"bill_number": item.bill_number,
									"bill_form_id": self.name,
									"number_operation": item.order_id.name if item.order_id.name else ' ' ,
									"type_coin": self.currency_id.name,
									"rate_exchange": round(item.exchange_rate , 2),
									"letter_capital_amount": round(item.bill_amount_total , 2),
									"expiration_days": item.interest_time,
									"expiration_date": str(item.bill_date_due) +  " 00:00:00" ,
									"letter_interest": item.interest,
									"letter_portes": item.freight_interest,
									"letter_igv": round(item.igv , 2),
									"letter_total_amount":  round(item.bill_amount_total , 2) ,
									"advance_total_amount": round(item.bill_amount_total , 2) ,
									"id_odoo": item.id
								}
						r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/advance_letter_detail/', data =json.dumps(line) , headers=headers)
						try:
							validate = r.json()
							item.id_loges = validate['data']['id_loges'] 
							
						except Exception as err:
							raise UserError(r.text)		
				else :
					raise UserError(r.text)

	def cancel(self):
		url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
		status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')

		super(BillForm,self).cancel()
		if status_api == "True":
			if self.method_registro == "Odoo" :
				headers = {'Content-type': 'application/json'}
				url_requests = str(url_api) + 'api/1.0/synchronization/from.odoo/advance_letter/'+str(self.id_loges) +'/'
				r = requests.delete(url_requests, headers=headers)
				for item in self.bill_ids:
					r = requests.delete(str(url_api) + 'api/1.0/synchronization/from.odoo/advance_letter_detail/' +str(item.id_loges)+'/', headers=headers)
		
class AdvancedBillLines(models.Model):
	_inherit = 'advanced.bill.lines'

	method_registro = fields.Char(string='Metodo de Registro',default="Odoo")
	id_loges = fields.Char(string='Id Loges')