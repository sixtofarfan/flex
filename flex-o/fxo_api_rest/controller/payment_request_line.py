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
# /api/v1/payment_request_line/<id>             GET     - Read one
# /api/v1/payment_request_line                  POST    - Create one
# /api/v1/payment_request_line/<id>             PUT     - Update one
# /api/v1/payment_request_line/<id>             DELETE  - Delete one

class ApiPaymentRequest(http.Controller):
    MANDATORY_FIELDS   =    ["name","amount"]
    RELATIONAL_FIELDS  =    ["partner_id","product_id","payment_request_id","currency_id","doc_type","doc_number",]
    OPTIONAL_FIELDS    =    ["id"]

    def data_return_payment_request_line(self,move):
        values = {key: move[key] for key in self.MANDATORY_FIELDS }
        values.update({key:int( move[key]['id']) for key in self.RELATIONAL_FIELDS })
        values.update({key:int( move[key]) for key in self.OPTIONAL_FIELDS })

        return values
    
    def return_success(self,move):
        data = self.data_return_payment_request_line(move)
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
            'error_mensaje': err if  err else "Error"
        }
        _logger.error("%s", err)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
    
    @http.route('/api/v1/payment_request_line/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_payment_request_line_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}

            l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('l10n_latam_identification_type_id'))])
            if len(l10n_latam_identification_type)==1:
                tipo_documento = l10n_latam_identification_type[0].id
            else :
                return self.erro_success("Tipo de Documento no encontrado")

            partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id')) ,('l10n_latam_identification_type_id','=',tipo_documento)])
            
            if len(partner) > 0:
                values.update({'partner_id':partner[0].id})
            else :
                return self.erro_success("Partner No encontrado")
            
            product_id = http.request.env['product.product'].sudo().search([('default_code', '=', kw.get('product_id') )])
            if len(product_id) > 0:
                values.update({'product_id':product_id[0].id})

            doc_type =  http.request.env['sale.order.type'].sudo().search([('code', '=', kw.get('doc_type')) ])
            if len(doc_type)==1:
                values.update({'doc_type':doc_type.id})
            else :
                return self.erro_success("Tipode  Documento no entonctrado ")
            
            doc_number =  http.request.env['sale.order'].sudo().search([('name', '=', kw.get('doc_number')) ])
            if len(doc_type)==1:
                values.update({'doc_number':doc_number.id})
            else :
                return self.erro_success("Pedido no encontrado ")
            
            payment_id =  http.request.env['fxo.payment.request'].sudo().search([('name', '=', kw.get('payment_request_id') ) ])
            if len(payment_id)==1:
                values.update({'payment_request_id':payment_id[0].id})
            else :
                return self.erro_success("Documento de Socilitud no Enconctrado  ")

            currency = http.request.env['res.currency'].sudo().search([('name', '=', kw.get('currency_id'))])
            if len(currency) > 0:
                values.update({'currency_id':currency[0].id})

            payment_request_line = http.request.env['fxo.payment.request.line'].sudo().create([values])

            return self.return_success(payment_request_line)
        except Exception as err:
            return self.erro_success(err.args) 
    
    @http.route('/api/v1/payment_request_line/<string:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_payment_request_line_put(self, ids=None,*args, **kw):
        payment_request_line = http.request.env['fxo.payment.request.line'].sudo().search([('id', '=', ids)])
        if len(payment_request_line) > 0:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS}

                l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('l10n_latam_identification_type_id'))])
                if len(l10n_latam_identification_type)==1:
                    tipo_documento = l10n_latam_identification_type[0].id
                else :
                    return self.erro_success("Tipo de Documento no encontrado")

                partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id')) ,('l10n_latam_identification_type_id','=',tipo_documento)])
                
                if len(partner) > 0:
                    values.update({'partner_id':partner[0].id})
                else :
                    return self.erro_success("Partner No encontrado")
                
                product_id = http.request.env['product.product'].sudo().search([('default_code', '=', kw.get('product_id') )])
                if len(product_id) > 0:
                    values.update({'product_id':product_id[0].id})

                doc_type =  http.request.env['sale.order.type'].sudo().search([('code', '=', kw.get('doc_type')) ])
                if len(doc_type)==1:
                    values.update({'doc_type':doc_type.id})
                else :
                    return self.erro_success("Tipode  Documento no entonctrado ")
                
                doc_number =  http.request.env['sale.order'].sudo().search([('name', '=', kw.get('doc_number')) ])
                if len(doc_type)==1:
                    values.update({'doc_number':doc_number.id})
                else :
                    return self.erro_success("Pedido no encontrado ")
                
                payment_id =  http.request.env['fxo.payment.request'].sudo().search([('name', '=', kw.get('payment_request_id') ) ])
                if len(payment_id)==1:
                    values.update({'payment_request_id':payment_id[0].id})
                else :
                    return self.erro_success("Documento de Socilitud no Enconctrado  ")

                currency = http.request.env['res.currency'].sudo().search([('name', '=', kw.get('currency_id'))])
                if len(currency) > 0:
                    values.update({'currency_id':currency[0].id})

                payment_request_line.sudo().write(values)
                return self.return_success(payment_request_line)
                
            except Exception as err:
                return self.erro_success(err.args) 
        else:
            return self.erro_success('No Encontrado')

    @http.route('/api/v1/payment_request_line/<string:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_payment_request_line_gets(self, ids=None, **get):
        payment_request_line = http.request.env['fxo.payment.request.line'].sudo().search([('id', '=', ids)])
        if len(payment_request_line)>0:
            return self.return_success(payment_request_line)
        else :
            return self.erro_success('error')
        
    @http.route('/api/v1/payment_request_line/delete/<string:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_payment_request_line_delete(self, ids=None,**kw):
        sale = http.request.env['fxo.payment.request.line'].sudo().search([('id', '=', ids)])
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
   