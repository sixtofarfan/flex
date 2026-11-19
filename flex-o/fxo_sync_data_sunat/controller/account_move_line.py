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
# /api/v1/account_move_line/<id>             GET     - Read one
# /api/v1/account_move_line                  POST    - Create one
# /api/v1/account_move_line/<id>             PUT     - Update one
# /api/v1/account_move_line/<id>             DELETE  - Delete one

class ApiAccountMove(http.Controller):
	MANDATORY_FIELDS   =    ["name"]
	RELATIONAL_FIELDS  =    [
								#"account_id","product_id","product_uom_id","company_id",
								"tax_ids","move_id","product_id"
							]
	OPTIONAL_FIELDS   =     [
							   "quantity","price_unit","discount","price_total","price_subtotal","id"
							]

	def data_return_account_move_line(self,move):
		values = {key: move[key] for key in self.MANDATORY_FIELDS }
		values.update({key:int( move[key]['id']) for key in self.RELATIONAL_FIELDS })
		values.update({key: move[key] for key in self.OPTIONAL_FIELDS if key in move})

		return values
	
	def return_success(self,move):
		data = self.data_return_account_move_line(move)
		json_data = {
			'success': True,
			'data':data,
			'status_code': 200
		} 
		return http.Response(json.dumps(json_data),content_type='application/json;charset=utf-8',status=200)
   
	def erro_success(self,err):
		data = {
			'error': True,
			'status_code': 400,
			'error_mensaje': err if  err else err
		}
		_logger.error("%s", err)
		return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
	
	@http.route('/api/v1/account_move_line/', type='http', auth="public", methods=['POST'],csrf=False)
	def api_account_move_line_post(self, *args, **kw):
		try:
			values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
			values.update({key:int( kw[key]['id']) for key in self.RELATIONAL_FIELDS })
			values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})

			account_move_line = http.request.env['account.move.line'].sudo().create(values)
			return self.return_success(account_move_line)
		except Exception as err:
 			return self.erro_success(err.args) 
	
	@http.route('/api/v1/account_move_line/<int:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
	def api_account_move_line_put(self,ids=None, *args, **kw):
		account_move_line = http.request.env['account.move.line'].sudo().search([('id', '=', ids)])
		if len(account_move_line) > 0:
			try:
				values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
				account_id = http.request.env['account.account'].sudo().search([('code', '=', kw.get('account_id')),('company_id','=',int(kw.get('company_id') ) )])
				if len(account_id) > 0:
					values.update({'account_id':account_id[0].id})
				else :
					values.pop('account_id')

				product_id = http.request.env['product.product'].sudo().search([('default_code', '=', kw.get('product_id') )])
				if len(account_id) > 0:
					values.update({'product_id':product_id[0].id})
				else :
					return self.erro_success("Producto No encontrado") 
				
				product_uom_id  = http.request.env['uom.uom'].sudo().search([('name', '=', kw.get('product_uom_id') )])
				if len(product_uom_id) > 0:
					values.update({'product_uom_id':product_uom_id[0].id})
				else :
					values.pop('analytic_account_id')
					
				name = kw.get('move_id')
				conpany = int( kw.get('company_id'))
				move_id =  http.request.env['account.move'].sudo().search([('name', '=',  name),('company_id','=',conpany)])

				if len(move_id) > 0:
					values.update({'move_id':move_id[0].id})
				else :
					return self.erro_success("Factua no Encontrada") 

				analytic_account_id = http.request.env['account.analytic.account'].sudo().search([('code', '=',  kw.get('analytic_account_id') ),('company_id','=',conpany )])
				if len(analytic_account_id) > 0:
					values.update({'analytic_account_id':analytic_account_id[0].id})


				values.update({key: int(kw[key]) for key in self.OPTIONAL_FIELDS if key in kw})

				account_move_line[0].sudo().write(values)

				return self.return_success(account_move_line)
			except Exception as err:
				return self.erro_success(err.args) 
		else:
			return self.erro_success('No Encontrado')

	@http.route('/api/v1/account_move_line/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
	def api_account_move_line_gets(self, ids=None, **get):
		account_move_line = http.request.env['account.move.line'].sudo().search([('id', '=', ids)])
		if len(account_move_line)>0:
			return self.return_success(account_move_line)
		else :
			return self.erro_success('error')
		
	@http.route('/api/v1/account_move_line/<int:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
	def api_account_move_line_delete(self, ids=None, *args, **kw):
		sale = http.request.env['account.move.line'].sudo().search([('id', '=', ids)])
		data = {}
		if len(sale) == 1:
			try:
				sale.unlink()
				data = {
				'success': True,
				'status_code': 200,
				}
				return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
			except Exception as err:
				return self.erro_success(err.args)
		else :
			data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
			return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   