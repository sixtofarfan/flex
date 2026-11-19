# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json
import pytz
import logging

from datetime import datetime
from psycopg2 import IntegrityError

from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.addons.base.models.ir_qweb_fields import nl2br
_logger = logging.getLogger(__name__)

# List of REST resources in current file:
#  (url prefix)                (method)     (action)
# /api/v1/payment_request/<id>             GET     - Read one
# /api/v1/payment_request                  POST    - Create one
# /api/v1/payment_request/<id>             PUT     - Update one
# /api/v1/payment_request/<id>             DELETE  - Delete one
  

class ApiPaymentRequest(http.Controller):
	MANDATORY_FIELDS   =    ["name","id_loges"]
	RELATIONAL_FIELDS  =    ["partner_id","user_request","company_id","catalog_payment_id","bank_id","order_id"]
	OPTIONAL_FIELDS    =    ["state","id","p_detraction","observation","type_payment","supplier_observation"]
	OPTIONAL_DATE      =    ["date_request"]


	def log_api_registro(self,codigo,tipo_solicitud,json_in,json_out,error_details,company_id,state):
		data  = {
					'name': True,
					'web_service': '/api/v1/payment_request/',
					'codigo':codigo,
					'tipo_solicitud':tipo_solicitud,
					'modelo': 'Solicitud de Pago',
					'json_in':json_in,
					'json_out':json_out,
					'error_details':error_details,
					'company_id':company_id,
					'state':state
				}
		log_api = http.request.env['api.logs.request'].sudo().create([data])

	def data_return_payment_request(self,move):
		values = {key: move[key] for key in self.MANDATORY_FIELDS }
		values.update({key:int( move[key]['id']) for key in self.RELATIONAL_FIELDS })
		values.update({key: move[key] for key in self.OPTIONAL_FIELDS if key in move})
		values.update({key: str(move[key]) for key in self.OPTIONAL_DATE if key in move})
		return values
	
	def return_success(self,move):
		data = self.data_return_payment_request(move)
		json_data = {
			'success': True,
			'data':data,
			'status_code': 200
		} 
		return http.Response(json.dumps(json_data),content_type='application/json;charset=utf-8',status=200)
   
	def erro_success(self,err,kw,metodo):
		data = {
			'error': True,
			'status_code': 400,
			'error_mensaje': err if  err else "error"
		}
		_logger.error("%s", err)
		#self.log_api_registro('400',metodo,str(kw),str(data),err,int(kw.get('company_id')),'error')

		return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
	
	@http.route('/api/v1/payment_request/', type='http', auth="public", methods=['POST'],csrf=False)
	def api_payment_request_post(self, *args, **kw):
		try:
			values = {key: kw[key] for key in self.MANDATORY_FIELDS}
			values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
			values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})
			l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('l10n_latam_identification_type_id') )])
			if len(l10n_latam_identification_type)==1:
				tipo_documento = l10n_latam_identification_type[0].id
			else :
				return self.erro_success("Tipo de Documento no encontrado",kw,'POST')

			partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id')) ,('l10n_latam_identification_type_id','=',tipo_documento)])
			if len(partner) > 0:
				values.update({'partner_id':partner[0].id})
			else :
				return self.erro_success("Partner No encontrado",kw,'POST')
			
			order_id  = http.request.env['sale.order'].sudo().search([('name', '=',kw.get('order_id') )])
			if len(order_id) > 0:
				values.update({'order_id':order_id.id})

			paid_to_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('paid_to_type') )])
			if len(paid_to_type)==1:
				tipo_documento = paid_to_type[0].id

				paid_to = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('paid_to')) ,('l10n_latam_identification_type_id','=',tipo_documento)])
				if len(paid_to) > 0:
					values.update({'paid_to':paid_to[0].id})

			user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('user_request'))])
			if len(user)==1:
				values.update({'user_request':user.id})
			else :
				return self.erro_success("Usuario Solicitante no encontrado",kw,'POST')

			company_id =  http.request.env['res.company'].sudo().search([('id', '=', int(kw.get('company_id'))) ])
			if len(company_id)==1:
				values.update({'company_id':company_id.id})
			else :
				return self.erro_success("Compañía no encontrada ",kw,'POST')
			
			catalog_payment_id =  http.request.env['einvoice.catalog.payment'].sudo().search([('code', '=', kw.get('catalog_payment_id') ) ])
			if len(catalog_payment_id) > 0:
				values.update({'catalog_payment_id':catalog_payment_id[0].id})
			else :
				return self.erro_success("Medio de Pago Invalido ",kw,'POST')

			payment_request_id = http.request.env['fxo.payment.request'].sudo().search([('name', '=', kw.get('name')) ])
			if len(payment_request_id) > 0:
				return self.return_success(payment_request_id)
			
			texto = kw.get('bank_id')
			if texto:
				bank =  json.loads(texto)
				bus = bank['acc_number'] 
				bank_id = http.request.env['res.partner.bank'].sudo().search([('acc_number', '=', bus ) ])
				
				if len(bank_id) > 0:
					values.update({'bank_id':bank_id[0].id})
				else :
					temp_bank_id  = http.request.env['res.bank'].sudo().search([('bic', '=', bank['bank_id'] ) ])
					if len(catalog_payment_id) > 0:
						values.update({'catalog_payment_id':catalog_payment_id[0].id})
					else :
						return self.erro_success("Medio de Pago Invalido ",kw,'POST')
					
					currency = http.request.env['res.currency'].sudo().search([('name', '=', bank['currency_id'])])


					temp = http.request.env['res.partner.bank'].sudo().create({
						
						"acc_number" : bank['acc_number'] ,
						"bank_id" : temp_bank_id.id,
						"type_of_account": int(bank['type_of_account']) ,
						"partner_id":partner[0].id,
						"currency_id":currency.id if currency.id else False,
					})
					values.update({'bank_id':temp[0].id})

			payment_request = http.request.env['fxo.payment.request'].sudo().create([values])
			self.log_api_registro('200','POST',str(kw),str(values),'',int(values.get('company_id')),'done')
			return self.return_success(payment_request)
		except Exception as err:
			return self.erro_success(err.args,kw,'POST') 
	
	@http.route('/api/v1/payment_request/<string:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
	def api_payment_request_put(self,ids=None, *args, **kw):
		payment_request = http.request.env['fxo.payment.request'].sudo().search([('id', '=', ids)])
		if len(payment_request) > 0 and payment_request.state in ['draft','confirm']:
			try:
				values = {key: kw[key] for key in self.MANDATORY_FIELDS}
				values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
				partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id'))])
				if len(partner) > 0:
					values.update({'partner_id':partner[0].id})
				else :
					return self.erro_success("Partner No encontrado",kw,'PUT')
				
				paid_to_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('paid_to_type') )])
				if len(paid_to_type)==1:
					tipo_documento = paid_to_type[0].id

					paid_to = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('paid_to')) ,('l10n_latam_identification_type_id','=',tipo_documento)])
					if len(paid_to) > 0:
						values.update({'paid_to':paid_to[0].id})

				user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('user_request'))])
				if len(user)==1:
					values.update({'user_request':user.id})
				else :
					return self.erro_success("Usuario Solicitante no encontrado",kw,'PUT')

				company_id =  http.request.env['res.company'].sudo().search([('id', '=', int(kw.get('company_id'))) ])
				if len(company_id)==1:
					values.update({'company_id':company_id.id})
				else :
					return self.erro_success("Compañía no encontrada ",kw,'PUT')

				payment_request.sudo().write(values)

				return self.return_success(payment_request)
			except Exception as err:
				return self.erro_success(err.args,kw,'PUT') 
		else:
			return self.erro_success('No Encontrado',kw,'PUT')

	@http.route('/api/v1/payment_request/<string:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
	def api_payment_request_gets(self, ids=None, **get):
		payment_request = http.request.env['fxo.payment.request'].sudo().search([('id', '=', ids)])
		if len(payment_request)>0:
			return self.return_success(payment_request)
		else :
			return self.erro_success('No Encontrado','','PUT')
		
	@http.route('/api/v1/payment_request/delete/<string:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
	def api_payment_request_delete(self, ids=None, *args, **kw):
		sale = http.request.env['fxo.payment.request'].sudo().search([('id', '=', ids)])
		data = {}
		if len(sale) == 1:
			try:
				sale.unlink()
				data = {
				'success': True,
				'status_code': 200,
				}
				#self.log_api_registro('201','DELETE','',str(data),int(1),'done')
				return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
			except Exception as err:
				return self.erro_success(err.args,'','DELETE')
		else :
			data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
			return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   