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
# /api/v1/account_move_relac/<id>             GET     - Read one
# /api/v1/account_move_relac                  POST    - Create one
# /api/v1/account_move_relac/<id>             PUT     - Update one
# /api/v1/account_move_relac/<id>             DELETE  - Delete one

class ApiAccountMove(http.Controller):
    MANDATORY_FIELDS   =    ["doc_invoice_relac","nro_comprobante"]
    RELATIONAL_FIELDS  =    ["move_id","type_document_id"]
    OPTIONAL_FIELDS   =     ["amount_currency","amount","bas_amount","tax_amount"]

    def data_return_account_move_relac(self,move):
        values = {key: move[key] for key in self.MANDATORY_FIELDS }
        values.update({key:int( move[key]['id']) for key in self.RELATIONAL_FIELDS })
        values.update({key: move[key] for key in self.OPTIONAL_FIELDS if key in move})
        return values
    
    def return_success(self,move):
        data = self.data_return_account_move_relac(move)
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
            'error_mensaje': err.args if  err.args else err
        }
        _logger.error("%s", err.args)
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
    
    @http.route('/api/v1/account_move_relac/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_account_move_relac_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            values.update({key:int(kw[key]) for key in self.RELATIONAL_FIELDS })
            values.update({key: move[key] for key in self.OPTIONAL_FIELDS if key in kw})
            account_move_relac = http.request.env['doc.invoice.relac'].sudo().create([values])
            return self.return_success(account_move_relac)
        except Exception as err:
            return self.erro_success(err) 
    
    @http.route('/api/v1/account_move_relac/<int:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_account_move_relac_put(self, *args, **kw):
        account_move_relac = http.request.env['doc.invoice.relac'].sudo().search([('id', '=', ids)])
        if len(account_move_relac) > 0:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS}

                return self.return_success(account_move_relac)
            except Exception as err:
                return self.erro_success(err) 
        else:
            return self.erro_success('No Encontrado')

    @http.route('/api/v1/account_move_relac/<int:ids>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_account_move_relac_gets(self, ids=None, **get):
        account_move_relac = http.request.env['doc.invoice.relac'].sudo().search([('id', '=', ids)])
        if len(account_move_relac)>0:
            return self.return_success(account_move_relac)
        else :
            return self.erro_success('error')
        
    @http.route('/api/v1/account_move_relac/<int:ids>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_account_move_relac_delete(self, ids=None, *args, **kw):
        sale = http.request.env['doc.invoice.relac'].sudo().search([('id', '=', ids)])
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
                return self.erro_success(err)
        else :
            data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   