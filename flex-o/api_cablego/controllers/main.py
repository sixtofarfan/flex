# -*- coding: utf-8 -*-
from logging import error
from odoo import fields
from odoo import http
from odoo.http import request
import hashlib
from datetime import datetime
from datetime import timedelta
import json,ssl
from decimal import Decimal

import requests as api_requests
import werkzeug.wrappers

import xmlrpc.client


def successful_response(status, dict_data):
	return werkzeug.wrappers.Response(
		status = status,
		content_type = 'application/json; charset=utf-8',
		#headers = None,
		response = json.dumps(dict_data),
	)

class CablegoApiController(http.Controller):


	@http.route(['/cablego'], type='http', methods=['GET'], csrf=False, auth="public", cors='*')
	def api_consultar_deuda(self, vat=None,type_doc=None,correo=False,**args):

		args = json.loads(json.dumps(request.httprequest.args))

		vat = args['vat']  if args['vat']  else False
		type_doc = args['type_doc']  if args['type_doc']  else False
		correo = args['email']  if args['email']  else False

		# Get request parameters from body
		partner = http.request.env['res.partner'].sudo().search([('signup_token', '=', args['acces_token'])])
		if len(partner) == 0:
			log_data = {
					"name": "Error Token",
					"web_service": "ConsultaCliente",
					"email":str(correo),
					"json_in": "type:" + str(type_doc) + "vat:  " +str(vat) + "  correo: " +str(correo),
			   		"company_id": request.env.user.company_id.id,
			   		"stages_id": 'error'
				}
			request.env['logs.request.cablego'].sudo().create(log_data)
			json_data = {
				'error': "Token Invalido",
				'status': 'Error'
			}
			return successful_response(200, json_data)

		else :
			values = {}
			company = request.env.user.company_id
			try:
				values = json.loads(request.httprequest.stream.read())
			except Exception as e:
				#REGISTO DE LOG DE ERROR
				company = request.env.user.company_id
			try:
				#Conexion con Base de datos
				common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(company.param_url_cablego),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
				uid = common.authenticate(company.param_db_cablego, company.param_username_cablego, company.param_password_cablego, {})
				#print (common.version())

				models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(company.param_url_cablego),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
				conex_result = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

				#Buscar el Cliente
				#l10n_latam.identification.type
				partner = []
				identification = []

				if correo == False:
					identification = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego,'l10n_latam.identification.type', 'search_read', [[['code_sunat', '=', type_doc]]],
						{'fields': ['id', 'name', 'code_sunat'], 'limit': 1})

					partner = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego,'res.partner', 'search_read', [[['vat', '=', vat],['l10n_latam_identification_type_id','=',identification[0]['id']]]],
						{'fields': ['id', 'name','email','vat','l10n_latam_identification_type_id'], 'limit': 1})

				else :
					partner = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego, 'res.partner', 'search_read', [[['email', '=', correo]]],
										{'fields': ['id', 'name', 'email', 'vat', 'l10n_latam_identification_type_id'], 'limit': 1})
					identification = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego, 'l10n_latam.identification.type', 'search_read', [[['id', '=', partner[0]['l10n_latam_identification_type_id'][0]]]],
										{'fields': ['id', 'name', 'code_sunat'], 'limit': 1})


				subscription = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego,'sale.subscription.line', 'search_read', [[['partner_id', '=', partner[0]['id']],['is_nubyx','=',True],['analytic_account_id.in_progress','=',True]]],
					{'fields': ['name','product_id'], 'limit': 10})
				
				product = models.execute_kw(company.param_db_cablego, uid, company.param_password_cablego,'product.product', 'search_read', [[['id', '=', subscription[0]['product_id'][0]]]],
					{'fields': ['product_rel_id'], 'limit': 1})

				json_data = {
					'name': partner[0]['name'],
					'email': partner[0]['email'],
					'vat': partner[0]['vat'],
					'type': identification[0]['code_sunat'],
					'product': product[0]['product_rel_id'],
				}
				
				log_data = {
						"name" : "/cablego",
						"web_service" : "ConsultaCliente",
						"json_in" : str(values),
						"company_id" : request.env.user.company_id.id,
						#'error_details': str(e),
						"email":str(correo),
						"stages_id" : 'done',
						"json_out" : str(json_data)
						}
				request.env['logs.request.cablego'].sudo().create(log_data)

			except Exception as e:
				log_data = {
						"name" : "",
						"web_service" : "ConsultaCliente",
						"json_in" : str(args),
						"email":str(correo),
						"company_id" : request.env.user.company_id.id,
						'error_details': str(e),
						"stages_id" : 'error'
						}
					
				#request.env['logs.request.cablego'].sudo().create(log_data)

				json_data = "No es Cliente"

			return successful_response(200, json_data)

	
	@http.route(['/cablego/auth'], type='http', methods=['get'], csrf=False, auth="public", cors='*')
	def api_token_cable(self, **args):
		json_data = {}
		try:
			value = json.loads(json.dumps(request.httprequest.args))
			request.session.authenticate(value['db'], value['login'], value['password'])
			login = request.env['ir.http'].session_info()
			partner = http.request.env['res.partner'].sudo().search([('id', '=', int(login['partner_id']) )])
			md5_email = partner.email
			if partner.signup_token == False:
				partner.signup_token = hashlib.md5(md5_email.encode('utf-8')).hexdigest()
			json_data ={
				'uid': partner.id,
				'acces_token': partner.signup_token
			}
			log_data = {
						"name" : "/cablego",
						"web_service" : "Token",
						"json_in" : str(value),
						"company_id" : request.env.user.company_id.id,
						#'error_details': str(e),
						"stages_id" : 'done',
						"json_out" : str(json_data)
						}
			request.env['logs.request.cablego'].sudo().create(log_data)

		except Exception as e:
			json_data = {
				'error': str(e),
				'status': 'Error'
			}
			log_data = {
						"name" : "/cablego",
						"web_service" : "Token",
						"json_in" : str(value),
						"company_id" : request.env.user.company_id.id,
						'error_details': str(e),
						"stages_id" : 'done',
						"json_out" : str(json_data)
						}
			request.env['logs.request.cablego'].sudo().create(log_data)

		return successful_response(200, json_data)

		
