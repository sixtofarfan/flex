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
# /api/v1/partner/<id>           GET     - Read one
# /api/v1/partner                POST    - Create one
# /api/v1/partner/<id>           PUT     - Update one
# /api/v1/partner/<id>           DELETE  - Delete one


class ApiPartner(http.Controller):
   MANDATORY_FIELDS = ["name","email"]

   OPTIONAL_FIELDS = ["vat","street","mobile", "phone","website","email","type","company_type","zip","is_supplier","is_customer","customer_rank","supplier_rank","function",
   "is_company","active","name_p","last_name","m_last_name","credit_limit","commercial_name","ref","id_loges","id"]
   
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
                    #'company_id':company_id,
                    'state':state
                }
      log_api = http.request.env['api.logs.request'].sudo().create([data])
   
   def data_return_partner(self,partner):
      data = {
         'id':partner.id,
         'name': partner.name,
         'l10n_latam_identification_type_id': {
           'name':partner.l10n_latam_identification_type_id.name,
           'code_sunat':partner.l10n_latam_identification_type_id.code_sunat,
           'id':partner.l10n_latam_identification_type_id.id
         },
         'vat': partner.vat,
         'company_type': partner.company_type,
         'is_supplier': partner.is_supplier,
         'is_customer': partner.is_customer,
         'is_employee': partner.is_employee,
         'customer_rank': partner.customer_rank,
         'supplier_rank': partner.supplier_rank,
         'type':partner.active,
         'street':partner.street,
         'zip': partner.zip,
         'phone': partner.phone,
         'mobile': partner.mobile,
         'email': partner.email,
         'website': partner.website,
         'country_id' :{
            'name': partner.country_id.name,
            'code': partner.country_id.code,
            'id  ': partner.country_id.id
         },
         'state_id' :{
            'name': partner.state_id.name,
            'code': partner.state_id.code,
            'id'  : partner.state_id.id
         },
         'province_id' :{
            'name': partner.province_id.name,
            'code': partner.province_id.code,
            'id'  : partner.province_id.id
         },
         'district_id' :{
            'name': partner.district_id.name,
            'code': partner.district_id.code,
            'id'  : partner.district_id.id
         },
         'parent_id': {
            'name': partner.parent_id.name,
            'vat':partner.parent_id.vat
         },
         'company_id':partner.company_id.name,
         'user_id':{
            'name': partner.user_id.name,
            'vat': partner.user_id.vat,
         },
         'is_company': partner.is_company,
         'active':partner.active,
         'name_p': partner.name_p,
         'last_name':partner.last_name,
         'm_last_name':partner.m_last_name,
         'credit_limit':partner.credit_limit,
         'property_payment_term_id': partner.property_payment_term_id.name,
         'commercial_name': partner.commercial_name, 
         'ref': partner.ref,

         
      }
      if len(partner.child_ids) > 0:
         child_ids = []
         for item in partner.child_ids:
            line = {
               'name': item.name,
               'street': item.street,
            }
            child_ids.append(line)
         data.update({'child_ids':child_ids})
      json_data = {
         'success': True,
         'data':data,
         'status_code': 200
      }    
      return json_data
   
   def return_success(self,partner):
      data = self.data_return_partner(partner)
      return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
   
   def erro_success(self,err,kw,metodo):
      data = {
            'error': True,
            'error_mensaje': err,
            'status_code': 300
         }
      self.log_api_registro('400',metodo,str(kw),str(data),err,int(kw.get('company_id')),'error')
      _logger.error("%s", err)
      return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
   @http.route('/api/v1/partner/', type='http', auth="public", methods=['POST'],csrf=False)
   def api_partner_post(self,country_id,vat=None,company_id=False,state_id=None,province_id=None,district_id=None,l10n_latam_identification_type_id='6',user_id=None ,property_payment_term_id=1,parent_id=None ,*args, **kw):
      data = {}
      try:
         values = {key: kw[key] for key in self.MANDATORY_FIELDS}
         values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
         l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', l10n_latam_identification_type_id)])
         if len(l10n_latam_identification_type)==1:
            values.update({'l10n_latam_identification_type_id':l10n_latam_identification_type.id})

         country =  http.request.env['res.country'].sudo().search([('code', '=', country_id)])
         if len(country)==1:
            values.update({'country_id':country.id})
         else:
            values.update({'country_id':173})

         state =  http.request.env['res.country.state'].sudo().search([('code', '=', state_id),('country_id','=',173)])
         if len(state)==1:
            values.update({'state_id':state.id})
         
         status_id =  http.request.env['catalog.100'].sudo().search([('code', '=', kw.get('status_id'))])
         if len(status_id)==1:
            values.update({'status_id':status_id.id})

         if kw.get('is_supplier')=='0':
            values.update({'supplier_rank':0})
            values.update({'is_supplier':False})
         else:
            values.update({'supplier_rank':1})
            values.update({'is_supplier':True})
         if kw.get('is_customer')=='0':
            values.update({'customer_rank':0})
            values.update({'is_customer':False})
         else:
            values.update({'customer_rank':1})
            values.update({'is_customer':True})

         province =  http.request.env['res.country.state'].sudo().search([('code', '=', province_id),('country_id','=',173)])
         if len(province)==1:
            values.update({'province_id':province.id})

         district = http.request.env['res.country.state'].sudo().search([('code', '=', district_id),('country_id','=',173)])
         if len(district)==1:
            values.update({'district_id':district.id})
         values.update({'method_registro':"web"})

         tipo_documento_user = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('import_sales_executive_type_document') )])
         if len(tipo_documento_user)==1:
            tipo_documento_user = tipo_documento_user[0].id
            user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('import_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',tipo_documento_user)])
            if len(user) > 0:
               values.update({'user_id':user[0].id})
         
         export_sales_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('export_sales_executive_type_document') )])
         if len(export_sales_executive_type_document)==1:
            export_sales_executive_type_document = export_sales_executive_type_document[0].id
            invoice_expo_user_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('export_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',export_sales_executive_type_document)])
            if len(invoice_expo_user_id) > 0:
               values.update({'invoice_expo_user_id':invoice_expo_user_id[0].id})

         collection_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('collection_executive_type_document') )])
         if len(collection_executive_type_document)==1:
            collection_executive_type_document = collection_executive_type_document[0].id
            collection_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('collection_executive_number_document')) ,('l10n_latam_identification_type_id','=',collection_executive_type_document)])
            if len(collection_id) > 0:
               values.update({'collection_id':collection_id[0].id})


         parent = http.request.env['res.partner'].sudo().search([('vat', '=', parent_id)])
         if len(parent)==1:
            values.update({'parent_id':parent.id})

          
         property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', property_payment_term_id)])
         if len(property_payment_term)==1:
            values.update({'property_payment_term_id':property_payment_term.id})
         if company_id :
            company  =  http.request.env['res.company'].sudo().search([('id', '=', int(company_id) )])
            if len(company)==1:
               values.update({'company_id':company.id})

         if kw.get('company_type') == "company":
            partner_cant = http.request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', l10n_latam_identification_type.id),('vat','=',vat)])
         
         else :
            partner_cant  = http.request.env['res.partner'].sudo().search([('email', '=', kw.get('email') )])

         if len(partner_cant) == 0:
            partner = http.request.env['res.partner'].sudo().create(values)
            if vat:
               partner.vat = vat
            else :
               partner.vat = ""
            self.log_api_registro('200','POST',str(kw),str(values),err,int(kw.get('company_id')),'done')
            return self.return_success(partner)
         else:
            self.log_api_registro('200','POST',str(kw),str(partner_cant),err,int(kw.get('company_id')),'done')

            return self.return_success(partner_cant)

      except Exception as err:
         if kw.get('company_type') == "company":
            partner_cant = http.request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', l10n_latam_identification_type.id),('vat','=',vat)])
         else :
            partner_cant  = http.request.env['res.partner'].sudo().search([('email', '=', kw.get('email') )])
         if len(partner_cant) > 0:
            return self.return_success(partner_cant[0])
         else :
            return self.erro_success(err.args,kw,'POST')
 
         return self.erro_success(err.args,kw,'POST')  
   
   @http.route('/api/v1/partner/id/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
   def api_partner_gets(self, ids=None, **get):
      partner = http.request.env['res.partner'].sudo().search([('id', '=', ids)])
      data = self.data_return_partner(partner)
      return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)   
   
   @http.route('/api/v1/partner/<string:type_documente>/<string:vat>', type='http', auth="public", methods=['get'], website=True,csrf=False)
   def api_partner_gets_id(self, type_documente=None,vat=None, **get):
      l10n_latam_identification_type_id = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', type_documente)])
      partner = http.request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', l10n_latam_identification_type_id.id),('vat','=',vat)])
      if len(partner) == 1:
         data = self.data_return_partner(partner)
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)  
      else :
         data = {'error': True,'status_code': 400 }
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)

   @http.route('/api/v1/partner/email/<string:vat>', type='http', auth="public", methods=['get'], website=True,csrf=False)
   def api_partner_gets_email(self, vat=None, **get):
      partner = http.request.env['res.partner'].sudo().search([('email','=',vat)])
      if len(partner) == 1:
         data = self.data_return_partner(partner)
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)  
      else: 
         data = {'error': True,'status_code': 400 }
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)


   @http.route('/api/v1/partner/<string:type_documente>/<string:vat>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
   def api_partner_delete_vat(self, ids=None, type_documente=None,vat=None, *args, **kw):
      l10n_latam_identification_type_id = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', type_documente)])
      partner = http.request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', l10n_latam_identification_type_id.id),('vat','=',vat)])
      data = {}
      if len(partner) == 1:
         try:
            partner.unlink()
            data = {
               'success': True,
               'status_code': 200
            }
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
         except Exception as err:
            return self.erro_success(err.args,kw,'delete')
      else :
         data = {'error': True,'status_code': 400 }
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
   @http.route('/api/v1/partner/<string:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
   def api_partner_delete(self, ids=None, *args, **kw):
      partner = http.request.env['res.partner'].sudo().search([('email', '=', ids)])
      data = {}
      if len(partner) == 1:
         try:
            partner.unlink()
            data = {
               'success': True,
               'status_code': 200
            }
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
         except Exception as err:
            return self.erro_success(err.args)
      else :
         data = {'error': True,'status_code': 400 }
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   

   @http.route('/api/v1/partner/<string:ids>', type='http', auth="public", methods=['put'], website=True,csrf=False)
   def api_partner_put(self, ids=None,country_id=None,company_id=False,state_id=None,province_id=None,district_id=None,l10n_latam_identification_type_id=None,user_id=None ,property_payment_term_id=None,parent_id=None , *args, **kw):
          
      partner = http.request.env['res.partner'].sudo().search([('email', '=', ids)])
      data = {}
      kw = {}
      try:
         values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
         values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
         values.update({'method_registro':"web"})
         l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', l10n_latam_identification_type_id)])
         if len(l10n_latam_identification_type)==1:
            values.update({'l10n_latam_identification_type_id':l10n_latam_identification_type.id})

         country =  http.request.env['res.country'].sudo().search([('code', '=', country_id)])
         if len(country)==1:
            values.update({'country_id':country.id})
         else:
            values.update({'country_id':173})

         state =  http.request.env['res.country.state'].sudo().search([('code', '=', state_id),('country_id','=',173)])
         if len(state)==1:
            values.update({'state_id':state.id})
         
         if kw.get('is_supplier')=='0':
            values.update({'supplier_rank':0})
            values.update({'is_supplier':False})
         else :
            values.update({'supplier_rank':1})
            values.update({'is_supplier':True})

         if kw.get('is_customer')=='0':
            values.update({'customer_rank':0})
            values.update({'is_customer':False})
         else :
            values.update({'customer_rank':1})
            values.update({'is_customer':True})

         province =  http.request.env['res.country.state'].sudo().search([('code', '=', province_id),('country_id','=',173)])
         if len(province)==1:
            values.update({'province_id':province.id})

         district = http.request.env['res.country.state'].sudo().search([('code', '=', district_id),('country_id','=',173)])
         if len(district)==1:
            values.update({'district_id':district.id})
         values.update({'method_registro':"web"})

         user = http.request.env['res.users'].sudo().search([('vat', '=', user_id)])
         if len(user)==1:
            values.update({'user_id':user.id})

         parent = http.request.env['res.partner'].sudo().search([('vat', '=', parent_id)])
         if len(parent)==1:
            values.update({'parent_id':parent.id})
          
         property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', property_payment_term_id)])
         if len(property_payment_term)==1:
            values.update({'property_payment_term_id':property_payment_term.id})
         
         if company_id :
            company  =  http.request.env['res.company'].sudo().search([('id', '=', int(company_id) )])
            if len(company)==1:
               values.update({'company_id':company.id})
         
         tipo_documento_user = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('import_sales_executive_type_document') )])
         if len(tipo_documento_user)==1:
            tipo_documento_user = tipo_documento_user[0].id
            user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('import_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',tipo_documento_user)])
            if len(user) > 0:
               values.update({'user_id':user[0].id})
         
         export_sales_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('export_sales_executive_type_document') )])
         if len(export_sales_executive_type_document)==1:
            export_sales_executive_type_document = export_sales_executive_type_document[0].id
            invoice_expo_user_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('export_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',export_sales_executive_type_document)])
            if len(invoice_expo_user_id) > 0:
               values.update({'invoice_expo_user_id':invoice_expo_user_id[0].id})

         collection_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('collection_executive_type_document') )])
         if len(collection_executive_type_document)==1:
            collection_executive_type_document = collection_executive_type_document[0].id
            collection_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('collection_executive_number_document')) ,('l10n_latam_identification_type_id','=',collection_executive_type_document)])
            if len(collection_id) > 0:
               values.update({'collection_id':collection_id[0].id})
               
         partner.sudo().write(values)
         return self.return_success(partner)
      except Exception as err:
         return self.erro_success(err.args)
   
   @http.route('/api/v1/partner/<string:type_documente>/<string:vat>', type='http', auth="public", methods=['put'], website=True,csrf=False)
   def api_partner_put_docum(self, type_documente=None,vat=None,company_id=False, country_id=None,state_id=None,province_id=None,district_id=None,l10n_latam_identification_type_id=None,user_id=None ,property_payment_term_id=None,parent_id=None , *args, **kw):   
      l10n_latam_identification_type_id = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', type_documente)])
      partner = http.request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', l10n_latam_identification_type_id.id),('vat','=',vat)])
      data = {}
      try:
         values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
         values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
         values.update({'method_registro':"web"})
         l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=',kw.get("l10n_latam_identification_type_id"))])
         if len(l10n_latam_identification_type_id)==1:
            values.update({'l10n_latam_identification_type_id':l10n_latam_identification_type_id.id})

         country =  http.request.env['res.country'].sudo().search([('code', '=', country_id)])
         if len(country)==1:
            values.update({'country_id':country.id})
         else:
            values.update({'country_id':173})

         state =  http.request.env['res.country.state'].sudo().search([('code', '=', state_id),('country_id','=',173)])
         if len(state)==1:
            values.update({'state_id':state.id})
         
         if kw.get('is_supplier')=='0':
            values.update({'supplier_rank':0})
            values.update({'is_supplier':False})
         else :
            values.update({'supplier_rank':1})
            values.update({'is_supplier':True})

         if kw.get('is_customer')=='0':
            values.update({'customer_rank':0})
            values.update({'is_customer':False})
         else :
            values.update({'customer_rank':1})
            values.update({'is_customer':True})

         province =  http.request.env['res.country.state'].sudo().search([('code', '=', province_id),('country_id','=',173)])
         if len(province)==1:
            values.update({'province_id':province.id})

         district = http.request.env['res.country.state'].sudo().search([('code', '=', district_id),('country_id','=',173)])
         if len(district)==1:
            values.update({'district_id':district.id})
         values.update({'method_registro':"web"})

         user = http.request.env['res.users'].sudo().search([('vat', '=', user_id)])
         if len(user)==1:
            values.update({'user_id':user.id})

         parent = http.request.env['res.partner'].sudo().search([('vat', '=', parent_id)])
         if len(parent)==1:
            values.update({'parent_id':parent.id})
          
         property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', property_payment_term_id)])
         if len(property_payment_term)==1:
            values.update({'property_payment_term_id':property_payment_term.id})
         
         if company_id :
            company  =  http.request.env['res.company'].sudo().search([('id', '=', int(company_id) )])
            if len(company)==1:
               values.update({'company_id':company.id})

         print('jose *********')
         print(values)
         print('Juan*********')
         print(kw)
         partner[0].sudo().write(values)
         return self.return_success(partner)
      except Exception as err:
         return self.erro_success(err.args)

   @http.route('/api/v1/partner/id/<string:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
   def api_partner_delete_id(self, ids=None, *args, **kw):
      partner = http.request.env['res.partner'].sudo().search([('id', '=', ids)])
      data = {}
      if len(partner) == 1:
         try:
            partner.unlink()
            data = {
               'success': True,
               'status_code': 200
            }
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
         except Exception as err:
            return self.erro_success(err.args)
      else :
         data = {'error': True,'status_code': 400 }
         return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
   @http.route('/api/v1/partner/id/<string:ids>', type='json', auth="public", methods=['put'], website=True,csrf=False)
   def api_partner_put_id(self, ids=None,country_id=None,company_id=False,state_id=None,province_id=None,district_id=None,l10n_latam_identification_type_id=None,user_id=None ,property_payment_term_id=None,parent_id=None , *args, **kw):
      kw = request.jsonrequest
      partner = http.request.env['res.partner'].sudo().search([('id', '=', ids)])
      data = {}
      try:
         values = {key: kw[key] for key in self.MANDATORY_FIELDS if key in kw}
         values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
         values.update({'method_registro':"web"})

         l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', l10n_latam_identification_type_id)])
         if len(l10n_latam_identification_type)==1:
            values.update({'l10n_latam_identification_type_id':l10n_latam_identification_type.id})

         country =  http.request.env['res.country'].sudo().search([('code', '=', country_id)])
         if len(country)==1:
            values.update({'country_id':country.id})
         else:
            values.update({'country_id':173})

         state =  http.request.env['res.country.state'].sudo().search([('code', '=', state_id),('country_id','=',173)])
         if len(state)==1:
            values.update({'state_id':state.id})
         
         if kw.get('is_supplier')=='0':
            values.update({'supplier_rank':0})
            values.update({'is_supplier':False})
         else :
            values.update({'supplier_rank':1})
            values.update({'is_supplier':True})

         if kw.get('is_customer')=='0':
            values.update({'customer_rank':0})
            values.update({'is_customer':False})
         else :
            values.update({'customer_rank':1})
            values.update({'is_customer':True})

         province =  http.request.env['res.country.state'].sudo().search([('code', '=', province_id),('country_id','=',173)])
         if len(province)==1:
            values.update({'province_id':province.id})

         district = http.request.env['res.country.state'].sudo().search([('code', '=', district_id),('country_id','=',173)])
         if len(district)==1:
            values.update({'district_id':district.id})
         values.update({'method_registro':"web"})

         user = http.request.env['res.users'].sudo().search([('vat', '=', user_id)])
         if len(user)==1:
            values.update({'user_id':user.id})

         parent = http.request.env['res.partner'].sudo().search([('vat', '=', parent_id)])
         if len(parent)==1:
            values.update({'parent_id':parent.id})
          
         property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', property_payment_term_id)])
         if len(property_payment_term)==1:
            values.update({'property_payment_term_id':property_payment_term.id})
         
         if company_id :
            company  =  http.request.env['res.company'].sudo().search([('id', '=', int(company_id) )])
            if len(company)==1:
               values.update({'company_id':company.id})
         
         tipo_documento_user = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('import_sales_executive_type_document') )])
         if len(tipo_documento_user)==1:
            tipo_documento_user = tipo_documento_user[0].id
            user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('import_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',tipo_documento_user)])
            if len(user) > 0:
               values.update({'user_id':user[0].id})
         
         export_sales_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('export_sales_executive_type_document') )])
         if len(export_sales_executive_type_document)==1:
            export_sales_executive_type_document = export_sales_executive_type_document[0].id
            invoice_expo_user_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('export_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',export_sales_executive_type_document)])
            if len(invoice_expo_user_id) > 0:
               values.update({'invoice_expo_user_id':invoice_expo_user_id[0].id})

         collection_executive_type_document = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('collection_executive_type_document') )])
         if len(collection_executive_type_document)==1:
            collection_executive_type_document = collection_executive_type_document[0].id
            collection_id = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('collection_executive_number_document')) ,('l10n_latam_identification_type_id','=',collection_executive_type_document)])
            if len(collection_id) > 0:
               values.update({'collection_id':collection_id[0].id})

         partner.sudo().write(values)
         return self.return_success(partner)
      except Exception as err:
         return self.erro_success(err.args)
   