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
# /api/v1/crm/<id>             GET     - Read one
# /api/v1/crm                  POST    - Create one
# /api/v1/crm/<id>             PUT     - Update one
# /api/v1/crm/<id>             DELETE  - Delete one

class ApiCRM_LEAD(http.Controller):

    MANDATORY_FIELDS   = ["name","email_from","phone"]
    RELATIONAL_FIELDS  = []
    OPTIONAL_FIELDS    = ["id","description"]

    def data_return_crm(self,crm):
        values = {key: crm[key] for key in self.MANDATORY_FIELDS if key in crm}
        values.update({key: crm[key] for key in self.OPTIONAL_FIELDS if key in crm})
        values.update({key: crm[key]['id'] for key in self.RELATIONAL_FIELDS if key in crm})
        return values
    
    def return_success(self,crm):
        data = self.data_return_crm(crm)
        json_data = {
            'success': True,
            'data':data
        } 
        return http.Response(json.dumps(json_data),content_type='application/json;charset=utf-8',status=200)
   
    def erro_success(self,err):
        data = {
            'error': True,
            'error_mensaje': err.args if  err.args else "Error"
        }
        _logger.error("%s", err.args)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)

    @http.route('/api/v1/crm/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_crm_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            #values = {key: kw[key] for key in self.RELATIONAL_FIELDS}
            values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
            crm = http.request.env['crm.lead'].sudo().create([values])
            return self.return_success(crm)
        except Exception as err:
            return self.erro_success(err)  

    @http.route('/api/v1/crm/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_crm_gets(self, ids=None, **get):
        crm = http.request.env['crm.lead'].sudo().search([('id', '=', ids)])
        data = self.data_return_crm(crm)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)   
    
    @http.route('/api/v1/crm/<int:ids>', type='http', auth="public", methods=['put'], website=True,csrf=False)
    def api_crm_put(self, ids=None, *args, **kw):
        crm = http.request.env['crm.lead'].sudo().search([('id', '=', ids)])
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            #values = {key: kw[key] for key in self.RELATIONAL_FIELDS}
            values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
            crm.sudo().write(values)
            return self.return_success(crm)
        except Exception as err:
            return self.erro_success(err)  
    
    @http.route('/api/v1/crm/<int:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_crm_delete(self, ids=None, *args, **kw):
        crm = http.request.env['crm.lead'].sudo().search([('id', '=', ids)])
        data = {}
        if len(crm) == 1:
            try:
                crm.unlink()
                data = {
                'success': True,
                }
                return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
            except Exception as err:
                return self.erro_success(err)
        else :
            data = {'error': True }
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   




    @http.route('/api/v1/crm/ide/<string:identify>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_crm_gets_identify(self, identify=None, **get):
        crm = http.request.env['crm.lead'].sudo().search(['|',('email_from', '=', identify),('phone', '=', identify)])
        data = self.data_return_crm(crm)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)   
    
    @http.route('/api/v1/crm/ide/<string:identify>', type='http', auth="public", methods=['put'], website=True,csrf=False)
    def api_crm_put_identify(self, identify=None, *args, **kw):
        crm = http.request.env['crm.lead'].sudo().search(['|',('email_from', '=', identify),('phone', '=', identify)])
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            #values = {key: kw[key] for key in self.RELATIONAL_FIELDS}
            values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
            crm.sudo().write(values)
            return self.return_success(crm)
        except Exception as err:
            return self.erro_success(err)  
    
    @http.route('/api/v1/crm/ide/<string:identify>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_crm_delete_identify(self, identify=None, *args, **kw):
        crm = http.request.env['crm.lead'].sudo().search(['|',('email_from', '=', identify),('phone', '=', identify)])
        data = {}
        if len(crm) == 1:
            try:
                crm.unlink()
                data = {
                'success': True,
                }
                return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
            except Exception as err:
                return self.erro_success(err)
        else :
            data = {'error': True }
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   



   