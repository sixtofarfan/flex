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
# /api/v1/product/<id>           GET     - Read one
# /api/v1/product                POST    - Create one
# /api/v1/product/<id>           PUT     - Update one
# /api/v1/product/<id>           DELETE  - Delete one

class ApiProduto(http.Controller):
    MANDATORY_FIELDS = ["name","type","default_code"]

    OPTIONAL_FIELDS = ["id","sale_ok","purchase_ok","barcode","list_price","standard_price"]

    def log_api_registro(self,codigo,tipo_solicitud,json_in,json_out,error_details,company_id,state):
        data  = {
                    'name': True,
                    'web_service': '/api/v1/product/',
                    'codigo':codigo,
                    'tipo_solicitud':tipo_solicitud,
                    'modelo': 'Producto',
                    'json_in':json_in,
                    'json_out':json_out,
                    'error_details':error_details,
                    'company_id':company_id,
                    'state':state
                }
        log_api = http.request.env['api.logs.request'].sudo().create([data])

    def data_return_product(self,product):
        values = {key: product[key] for key in self.MANDATORY_FIELDS if key in product}
        values.update({key: product[key] for key in self.OPTIONAL_FIELDS if key in product})
        return values
    
    def return_success(self,product):
        data = self.data_return_product(product)
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
            'error_mensaje': err.args if  err.args else "Error"
        }
        self.log_api_registro('400',metodo,str(kw),str(data),err,int(kw.get('company_id')),'error')

        _logger.error("%s", err.args)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
    @http.route('/api/v1/product/<string:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_product_gets(self, ids=None, **get):
        product = http.request.env['product.template'].sudo().search([('default_code', '=', ids)])
        if len(product) > 0:
            
            return self.return_success(product)
        else:
            return self.erro_success(product,'','GET')
   
    @http.route('/api/v1/product/id/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_product_gets_id(self, ids=None, **get):
        product = http.request.env['product.template'].sudo().search([('id', '=', ids)])
        if len(product) > 0:
            return self.return_success(product)
        else:
            return self.erro_success(product)


    @http.route('/api/v1/product/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_product_post(self,company_id=0, *args, **kw):
        values = self.data_return_product(kw)
        product = http.request.env['product.template'].sudo().search([('default_code', '=', values.get('default_code'))])
        if len(product) == 0: 
            try:
                values.update({'method_registro':"web"})
                if int(company_id) >  0:
                    property_account_expense_id  = http.request.env['account.account'].sudo().search([('code', '=', kw.get('property_account_expense_id')),('company_id','=',company_id ) ])
                    if len(property_account_expense_id) > 0:
                        values.update({'property_account_expense_id':property_account_expense_id[0].id})
                    
                    property_account_income_id = http.request.env['account.account'].sudo().search([('code', '=', kw.get('property_account_income_id')),('company_id','=',company_id ) ])
                    
                    if len(property_account_expense_id) > 0:
                        values.update({'property_account_income_id':property_account_income_id[0].id})


                    company  =  http.request.env['res.company'].sudo().search([('id', '=', company_id) ])
                    if len(company)==1:
                        values.update({'company_id':company.id})

                product =  http.request.env['product.template'].sudo().create(values)
                self.log_api_registro('200','POST',str(kw),str(values),'',int(values.get('company_id')),'done')

                return self.return_success(product)
            except Exception as err:
                values.update({'method_registro':"web"})
                product = http.request.env['product.template'].sudo().search([('default_code', '=', kw.get('default_code'))])
                if len(product) > 0:
                    self.log_api_registro('200','POST',str(kw),str(product),'',int(values.get('company_id')),'done')
                    return self.return_success(product)
                else :
                    return self.erro_success(err)
        else :
            return self.erro_success('err')
     
    @http.route('/api/v1/product/<string:ids>', type='http', auth="public", methods=['put'], website=True,csrf=False)
    def api_product_put(self, ids=None, *args, **kw):  
        product = http.request.env['product.template'].sudo().search([('default_code', '=', ids)])
        try:
            values = self.data_return_product(kw)
            product.sudo().write(values)
            self.log_api_registro('201','PUT',str(kw),str(values),'',int(values.get('company_id')),'done')
            return self.return_success(product)
        except Exception as err:
            return self.erro_success(err)
    
    @http.route('/api/v1/product/<string:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_product_delete(self, ids=None, *args, **kw):
      product = http.request.env['product.template'].sudo().search([('default_code', '=', ids)])
      data = {}
      if len(product) == 1:
         try:
            product.unlink()
            data = {
               'success': True,
               'status_code': 200
            }
            self.log_api_registro('201','DELETE','',str(data),int(values.get('company_id')),'done')
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
         except Exception as err:
            return self.erro_success(err)
      else :
         data = {'error': True ,'status_code': 400}
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
    @http.route('/api/v1/product/id/<int:ids>', type='http', auth="public", methods=['put'], website=True,csrf=False)
    def api_product_put_id(self, ids=None, *args, **kw):  
        product = http.request.env['product.template'].sudo().search([('id', '=', ids)])
        try:
            values = self.data_return_product(kw)
            product.sudo().write(values)
            self.log_api_registro('201','PUT',str(kw),str(values),'',int(values.get('company_id')),'done')
            return self.return_success(product)
        except Exception as err:
            return self.erro_success(err)
    
    @http.route('/api/v1/product/id/<int:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_product_delete_id(self, ids=None, *args, **kw):
      product = http.request.env['product.template'].sudo().search([('id', '=', ids)])
      data = {}
      if len(product) == 1:
         try:
            product.unlink()
            data = {
               'success': True,
               'status_code': 200
            }
            self.log_api_registro('201','DELETE','',str(data),int(values.get('company_id')),'done')
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
         except Exception as err:
            return self.erro_success(err)
      else :
         data = {'error': True ,'status_code': 400}
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   