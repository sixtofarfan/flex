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
# /api/v1/sale_line/<id>             GET     - Read one
# /api/v1/sale_line                  POST    - Create one
# /api/v1/sale_line/<id>             PUT     - Update one
# /api/v1/sale_line/<id>             DELETE  - Delete one

class ApiSaleLine(http.Controller):
    MANDATORY_FIELDS   = ["name","price_unit","price_subtotal","product_uom_qty","customer_lead"]
    RELATIONAL_FIELDS  = ["product_id","order_id"]
    OPTIONAL_FIELDS    = ["id","id_loges"]

    def log_api_registro(self,codigo,tipo_solicitud,json_in,json_out,error_details,company_id,state):
        data  = {
                    'name': True,
                    'web_service': '/api/v1/sale_line/',
                    'codigo':codigo,
                    'tipo_solicitud':tipo_solicitud,
                    'modelo': 'Linea Pedido',
                    'json_in':json_in,
                    'json_out':json_out,
                    'error_details':error_details,
                    'company_id':company_id,
                    'state':state
                }
        log_api = http.request.env['api.logs.request'].sudo().create([data])

    def data_return_sale_linet(self,sale_line):
        values = {key: sale_line[key] for key in self.MANDATORY_FIELDS }
        values.update({key: sale_line[key]['id'] for key in self.RELATIONAL_FIELDS })
        values.update({key: sale_line[key] for key in self.OPTIONAL_FIELDS if key in sale_line})
        return values
    
    def return_success(self,sale_line):
        data = self.data_return_sale_linet(sale_line)
        json_data = {
            'success': True,
            'data':data,
            'status_code': 200
        } 
        
        return http.Response(json.dumps(json_data),content_type='application/json;charset=utf-8',status=200)
   
    def erro_success(self,err,j,k):
        data = {
            'error': True,
            'status_code': 400,
            'error_mensaje': err ,
            'json':j
        }
        #company = int(j.get('company_id')) if j.get('company_id') else False
        #self.log_api_registro('400','POST',str(j),str(k),err,'','error')

        _logger.error("%s", err)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
    
    @http.route('/api/v1/sale_line/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_sale_line_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            order = http.request.env['sale.order'].sudo().search([('id', '=', kw.get('order_id'))])
            if len(order) > 0:
                values.update({'order_id':order[0].id})
            product = http.request.env['product.product'].sudo().search([('default_code', '=', kw.get('product_id'))])
            if len(product) > 0:
                values.update({'product_id':product[0].id})

            sale_line = http.request.env['sale.order.line'].sudo().create([values])
            
            #self.log_api_registro('200','POST',str(kw),str(values),'','','done')
            return self.return_success(sale_line)
        except Exception as err:
            return self.erro_success(err.args,kw,values) 
    
    @http.route('/api/v1/sale_line/<int:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_sale_line_put(self,ids=None, *args,  **kw):
        sale_line = http.request.env['sale.order.line'].sudo().search([('id', '=', ids)])
        if len(sale_line) > 0:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS}
                order = http.request.env['sale.order'].sudo().search([('name', '=', kw.get('order_id'))])
                if len(order) > 0:
                    values.update({'order_id':order[0].id})
                product = http.request.env['product.product'].sudo().search([('default_code', '=', kw.get('product_id'))])
                if len(product) > 0:
                    values.update({'product_id':product[0].id})
                sale_line[0].sudo().write(values)
                #self.log_api_registro('201','PUT',str(kw),str(values),err.args,'','done')
                return self.return_success(sale_line)
            except Exception as err:
                return self.erro_success(err.args,kw,values) 
        else:
            return self.erro_success('No Encontrado',kw,'')

    @http.route('/api/v1/sale_line/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_sale_line_gets(self, ids=None, **get):
        sale_line = http.request.env['sale.order.line'].sudo().search([('id', '=', ids)])
        if len(sale_line)>0:
            return self.return_success(sale_line)
        else :
            return self.erro_success('error','','')
        
    @http.route('/api/v1/sale_line/<int:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_sale_line_delete(self, ids=None, *args, **kw):
        sale = http.request.env['sale.order.line'].sudo().search([('id', '=', ids)])
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
                return self.erro_success(err.args,'','')
        else :
            #self.log_api_registro('400','Delete',str(kw),'',err,'done')

            data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
