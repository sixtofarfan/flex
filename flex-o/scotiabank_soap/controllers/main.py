# -*- coding: utf-8 -*-
from odoo import fields
from odoo import http
from odoo.http import request
from datetime import datetime
from datetime import timedelta
import json,ssl
from decimal import Decimal

import requests as api_requests
import werkzeug.wrappers

from xmlrpc import client as xmlrpclib

URL = ""
DATABASE = ""
username = ""
password = ""

GLOBAL_CURRENCY_USD = 0
GLOBAL_CURRENCY_PEN = 0

GLOBAL_JOURNAL_USD = 0
GLOBAL_JOURNAL_PEN = 0

GLOBAL_ACCOUNT_USD = 0
GLOBAL_ACCOUNT_PEN = 0

def successful_response(status, dict_data):
    return werkzeug.wrappers.Response(
        status = status,
        content_type = 'application/json; charset=utf-8',
        #headers = None,
        response = json.dumps(dict_data),
    )

def error_response(status, error, error_descrip):
    return werkzeug.wrappers.Response(
        status = status,
        content_type = 'application/json; charset=utf-8',
        #headers = None,
        response = json.dumps({
            'error':         error,
            'error_message': error_descrip,
        }),
    )


class BancoScotiabankController(http.Controller):

    @http.route('/Scotiabank/ConsultarDeuda', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_consultar_deuda(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        values = json.loads(request.httprequest.stream.read())
        company = request.env.user.company_id
        log_data = {
                "name" : "",
                "web_service" : "ConsultarDeuda",
                "json_in" : str(values),
                "company_id" : request.env.user.company_id.id,
                "stages_id" : 'error'
                }
            
        event_obj = request.env['logs.request.scotiabank'].sudo().create(log_data)
        
                #EXTRAER DATOS DE CONEXION Y CONFIGURACIÓN
        company = request.env.user.company_id

        URL = company.stb_param_url
        DATABASE = company.stb_param_db
        username = company.stb_param_username
        password = company.stb_param_password
        try:
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            uid = common.authenticate(DATABASE, username, password, {})
    
            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            conex_result = models.execute_kw(DATABASE, uid, password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

        except Exception as e:
            json_data = { 'respuesta' : "NO SE PUDO REALIZAR LA TRANSACCIÓN" }
            return successful_response (200, json_data)
        
        json_data = { 
            'respuesta' : "0210F22080010E80800000000000000000183550000000000000000127150354024286012706520900            000000000056    6040023028902                      REC     890 016953560              ATARAMA GUTIERREZ DO0100001319584600100000000000000000000          001604V RECIBO DE FACTURACIÓN                                                           00001     001                6953560                 000000022.3000000022.3"
        }
        return successful_response (200, json_data)


    @http.route('/Scotiabank/Notificarpago', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_notificar_pago(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        # Get request parameters from body
        values = {}

        return successful_response (200, values)



    @http.route('/Scotiabank/ExtornarPago', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_extornar_pago(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        # Get request parameters from body
        values = {}

        return successful_response (200, values)
