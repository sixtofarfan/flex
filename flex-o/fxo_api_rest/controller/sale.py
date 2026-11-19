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
# /api/v1/sale/<id>             GET     - Read one
# /api/v1/sale                  POST    - Create one
# /api/v1/sale/<id>             PUT     - Update one
# /api/v1/sale/<id>             DELETE  - Delete one

class ApiSale(http.Controller):

    MANDATORY_FIELDS   = ["name",]
    RELATIONAL_FIELDS  = ["partner_id","company_id"]
    OPTIONAL_FIELDS    = ["type_service","internal_ref","internal_ref_child","internal_ref_grandchild",
                          "internal_ref_great_grandson","shipper_name","consignne_name","via","salesman_name",
                          "tracing_name","operations_name","flight_number","total_volumen","total_wieght",
                          "origin_country","origin_port","destination_country","destination_city","foreign_agent_name",
                          "naviera_name","delivery_master_number","delivery_child_number","delivery_grandchild_number",
                          "delivery_great_grandson_number","cda_number","year_dam_number","regime_name","dispach_type",
                          "sada_type","name_booking","load_type","rights_payments","amount_untaxed1","freight_value",
                          "safe_value","cif_value","ady_total","amount_tax1","ipm_total","perception_total","terminal_name",
                          "cda_number_perception","freight_condition","note","quotation","client_order_ref","id_loges","id"]

    OPTIONAL_DATE       = ["date_order","flight_date","numbering_date","finishing_date","date_invoicing","date_verify","date_done"]

    def log_api_registro(self,codigo,tipo_solicitud,json_in,json_out,error_details,company_id,state):
        data  = {
                    'name': True,
                    'web_service': '/api/v1/sale/',
                    'codigo':codigo,
                    'tipo_solicitud':tipo_solicitud,
                    'modelo': 'Pedido',
                    'json_in':json_in,
                    'json_out':json_out,
                    'error_details':error_details,
                    'company_id':company_id,
                    'state':state
                }
        log_api = http.request.env['api.logs.request'].sudo().create([data])

    def data_return_sale(self,sale):
        values = {key: sale[key] for key in self.MANDATORY_FIELDS if key in sale}
        values.update({key: sale[key]['id'] for key in self.RELATIONAL_FIELDS if key in sale})
        values.update({key: sale[key] for key in self.OPTIONAL_FIELDS if key in sale})
        values.update({key: str(sale[key]) for key in self.OPTIONAL_DATE if key in sale})
        line = []
        for item in sale.order_line:
            dato = {
                'id':item.id,
                'name':item.name,
                'product_id': item.product_id.id,
                'price_unit': item.price_unit,
                'product_uom_qty': item.product_uom_qty,
                'price_subtotal': item.price_subtotal
            }
            line.append(dato)
        values.update({'order_line':line})
        return values
    
    def return_success(self,sale):
        data = self.data_return_sale(sale)
        json_data = {
            'success': True,
            'data':data,
            'status_code': 200
        } 
        return http.Response(json.dumps(json_data),content_type='application/json;charset=utf-8',status=200)
   
    def erro_success(self,err,kw):
        data = {
            'error': True,
            'error_mensaje': err if  err else "Error",
            'status_code': 400,
        }
       # self.log_api_registro('400','POST',str(kw),str(data),err,int(kw.get('company_id')),'error')

        _logger.error("%s", err)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)

    @http.route('/api/v1/sale/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_sale_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            values = {key: kw[key] for key in self.RELATIONAL_FIELDS if key in kw}
            values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
            values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})

            l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('l10n_latam_identification_type_id'))])
            if len(l10n_latam_identification_type)==1:
                tipo_documento = l10n_latam_identification_type[0].id
            else :
                return self.erro_success("Tipo de Documento no encontrado",kw)

            partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id')) ,('l10n_latam_identification_type_id','=',tipo_documento)])

            if len(partner) > 0:
                values.update({'partner_id':partner[0].id})
            else :
                return self.erro_success("Partner No encontrado",kw)

            
            values.update({'company_id':int(values.get('company_id'))})
            
            type_id = http.request.env['sale.order.type'].sudo().search([('code', '=', kw.get('type_id'))])
            
            if len(type_id) > 0:
                values.update({'type_id':type_id.id}) 
            else :
                return self.erro_success("Tipo  de Pedido Incorrecto",str(kw))
            if kw.get('situation_payment')=='1':
                values.update({'situation_payment':False})
            else : 
                values.update({'situation_payment':True})
            analytic_account_id = http.request.env['account.analytic.account'].sudo().search([('code', '=', kw.get('analytic_account_id') ),('company_id','=',int(kw.get('company_id') )) ])
            if len(analytic_account_id) > 0:
                    values.update({'analytic_account_id':analytic_account_id[0].id})

            name = kw.get('name') 
            sale_cant = http.request.env['sale.order'].sudo().search([('name', '=', name),('company_id','=',int(values.get('company_id') ) )])
            if len(sale_cant) > 0:
                #self.log_api_registro('200','POST',(kw),str(values),'',int(values.get('company_id')),'done')
                return self.return_success(sale_cant)
            else :
                sale = http.request.env['sale.order'].sudo().create([values])
                if len(type_id) > 0:
                    sale.name = str(name)
                else :
                    sale.name = name 
                #self.log_api_registro('200','POST',str(kw),str(values),'',int(values.get('company_id')),'done')
                return self.return_success(sale)
        except Exception as err:
            return self.erro_success(err.args,kw)  
    
    @http.route('/api/v1/sale/id/<string:ids>', type='http', auth="public", methods=['GET'], website=True,csrf=False)
    def api_sale_gets_new(self, ids=None, **get):
        print("get " + str(ids))
        sale = http.request.env['sale.order'].sudo().search([('id', '=', ids)])
        if len(sale) >0 :
            return self.return_success(sale)
        else:
            return self.erro_success('Pedido No encontrado','') 
    
    @http.route('/api/v1/sale/id/<string:ids>', type='json', auth="public", methods=['put'], website=True,csrf=False)
    def sale_put_id_new(self, ids=None, **kw):
        print('put' +str( ids))
        kw = request.jsonrequest
        sale = http.request.env['sale.order'].sudo().search([('id', '=', int(ids))])
        if len(sale) == 1:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
                values.update({key: kw[key] for key in self.RELATIONAL_FIELDS if key in kw})
                values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
                values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})
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
                    
                type_id = http.request.env['sale.order.type'].sudo().search([('code', '=', kw.get('type_id'))])
                
                if len(type_id) > 0:
                    values.update({'type_id':type_id.id}) 
                else :
                    return self.erro_success("Tipo  de Pedido Incorrecto")
                if kw.get('situation_payment')=='1':
                    values.update({'situation_payment':False})
                else : 
                    values.update({'situation_payment':True})
                    
                values.update({'company_id':int(values.get('company_id'))})   
                sale.sudo().write(values)
                values.update({'status_code':'200'})   
                return values
            except Exception as err:
                return self.erro_success(err,'')  
        else:
            return self.erro_success('Pedido No encontrado','')
    
    @http.route('/api/v1/sale/id/<string:ids>', type='http', methods=['DELETE'], csrf=False, auth="public", cors='*')
    def sale_delete(self, ids=None, *args, **kw):
        print('delete' +str( ids))
        sale = http.request.env['sale.order'].sudo().search([('id', '=', int(ids) )])

        data = {}
        if len(sale) == 1:
            try:
                sale.unlink()
                data = {
                'success': True,
                'status_code': 200
                }
                return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
            except Exception as err:
                return self.erro_success(err.args,'')
        else :
            data = {'error': True ,'status_code': 400}
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   