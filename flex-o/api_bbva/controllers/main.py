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

import xmlrpc.client

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

def error_response_401__invalid_token():
    error_descrip = "Token is expired or invalid!"
    error = 'invalid_token'
    #_logger.error(error_descrip)
    return error_response(401, error, error_descrip)

def error_response_400__no_access_token():
    error_descrip = "No access token was provided in request header!"
    error = 'no_access_token'
    #_logger.error(error_descrip)
    return error_response(400, error, error_descrip)

def error_response_400__no_access_platform():
    error_descrip = "No platform was provided in request header!"
    error = 'no_access_platform'
    #_logger.error(error_descrip)
    return error_response(400, error, error_descrip)

def asignar_configuracion(_url, _db, _username, _password, _currency_usd, _currency_pen, _journal_usd, _journal_pen, _account_usd, _account_pen):
    global URL
    global DATABASE
    global username
    global password

    global GLOBAL_CURRENCY_USD
    global GLOBAL_CURRENCY_PEN

    global GLOBAL_JOURNAL_USD
    global GLOBAL_JOURNAL_PEN

    global GLOBAL_ACCOUNT_USD
    global GLOBAL_ACCOUNT_PEN

    URL = _url
    DATABASE = _db
    username = _username
    password = _password

    GLOBAL_CURRENCY_USD = _currency_usd
    GLOBAL_CURRENCY_PEN = _currency_pen

    GLOBAL_JOURNAL_USD = _journal_usd
    GLOBAL_JOURNAL_PEN = _journal_pen

    GLOBAL_ACCOUNT_USD = _account_usd
    GLOBAL_ACCOUNT_PEN = _account_pen

    return True

def json_response(_servicio, _cabecera, _codigo, _descripcion):
    null = None
    json_data_response = {
        _servicio :   {
            "recaudosRs" : {
                "cabecera" : _cabecera,
                "detalle" : {
                    "respuesta" : {
                        "codigo" : _codigo,
                        "descripcion" : _descripcion
                    },
                    "transaccion" : null
                }
            }
        }
    }
    return json_data_response

class BancoApiController(http.Controller):


    @http.route('/ConsultarDeuda', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_consultar_deuda(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        # Get request parameters from body
        values = {}
        try:
            values = json.loads(request.httprequest.stream.read())

            api_cabecera = values['ConsultarDeuda']['recaudosRq']['cabecera']
            api_referencia = values['ConsultarDeuda']['recaudosRq']['detalle']['transaccion']['numeroReferenciaDeuda']

            #REGISTO DE LOG
            log_data = {
                "name" : api_cabecera['operacion']['codigoOperacion'],
                "web_service" : "ConsultarDeuda",
                "referencia_deuda" : api_referencia,
                "numero_documento" : "",
                "codigoOperacion" : api_cabecera['operacion']['codigoOperacion'],
                "numeroOperacion" : api_cabecera['operacion']['numeroOperacion'],
                "codigoBanco" : api_cabecera['operacion']['codigoBanco'],
                "codigoConvenio" : api_cabecera['operacion']['codigoConvenio'],
                "canalOperacion" : api_cabecera['operacion']['canalOperacion'],
                "codigoOficina" : api_cabecera['operacion']['codigoOficina'],
                "fechaOperacion" : api_cabecera['operacion']['fechaOperacion'], 
                "horaOperacion" : api_cabecera['operacion']['horaOperacion'],

                "json_in" : json.dumps(values, indent=4, sort_keys=True),
                "company_id" : request.env.user.company_id.id,
                "stages_id" : 'new'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)

        except Exception as e:
            #REGISTO DE LOG DE ERROR
            log_data = {
                "name" : "",
                "web_service" : "ConsultarDeuda",
                "json_in" : str(values),
                "company_id" : request.env.user.company_id.id,
                'error_details': str(e),
                "stages_id" : 'error'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)
            json_data = json_response("ConsultarDeudaResponse", None, "3000", "FORMATO DE TRAMA NO VÁLIDO")
            return successful_response (200, json_data)

        #EXTRAER DATOS DE CONEXION Y CONFIGURACIÓN
        company = request.env.user.company_id

        asignar_configuracion(company.param_url, company.param_db, company.param_username, company.param_password,
            company.param_currency_usd, company.param_currency_pen, company.param_journal_usd, company.param_journal_pen,
            company.param_account_usd, company.param_account_pen)

        error_data = ""

        try:

            #Conexion con Base de datos...
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            uid = common.authenticate(DATABASE, username, password, {})
            #print (common.version())

            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            conex_result = models.execute_kw(DATABASE, uid, password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})


            partner = models.execute_kw(DATABASE, uid, password,'res.partner', 'search_read', [[['ref', '=', api_referencia]]],
                {'fields': ['id', 'name'], 'limit': 1})

            if partner:
                partner_id = partner[0]['id']
                partner_name = partner[0]['name']

                moneda_convenio = False
                if int(api_cabecera['operacion']['codigoConvenio']) == int(company.bbva_contract_usd):
                    moneda_convenio = company.param_currency_usd

                elif int(api_cabecera['operacion']['codigoConvenio']) == int(company.bbva_contract_pen):
                    moneda_convenio = company.param_currency_pen


                if moneda_convenio:

                    invoice_ids = models.execute_kw(DATABASE, uid, password,
                        'account.move', 'search_read',
                        [[['type', '=', 'out_invoice'], 
                            ['state', '=', 'posted'], 
                            ['currency_id', '=', moneda_convenio],
                            ['invoice_payment_state', '=', 'not_paid'],
                            ['partner_id', '=', partner_id ]]],
                        {'fields': ['ref', 'glosa', 'invoice_date', 'invoice_date_due', 'amount_residual'], 'limit': 8, 'order':'invoice_date_due asc'})

                    if invoice_ids:

                        vals = []
                        for invoice in invoice_ids:
                            fecha_emision = datetime.strptime(invoice['invoice_date'], '%Y-%m-%d').strftime('%Y%m%d')
                            fecha_vcmto = datetime.strptime(invoice['invoice_date_due'], '%Y-%m-%d').strftime('%Y%m%d')
                            vals.append(
                                {
                                    "numero" : invoice['ref'],
                                    "descripcion" : "Pago unico",
                                    "fechaEmision" : fecha_emision,
                                    "fechaVencimiento" : fecha_vcmto,
                                    "importeDeuda" : format(round(invoice['amount_residual'],2),".2f"), #"450.50",
                                    "importeDeudaMinima" : "1", #format(round(invoice['amount_residual'],2),".2f"), #"50.00",
                                    "indicadorRestriccPago" : "0",
                                    "cantidadSubconceptos" : "0"
                                })

                        json_data = {
                            "ConsultarDeudaResponse":   {
                                "recaudosRs" : {
                                    "cabecera" : api_cabecera,
                                    "detalle" : {
                                        "respuesta" : {
                                            "codigo" : "0001",
                                            "descripcion" : "Operación realizada con éxito."
                                        },
                                        "transaccion" : {
                                            "numeroReferenciaDeuda" : api_referencia,
                                            "nombreCliente" : partner_name,
                                            "numeroOperacionEmpresa" : "",
                                            "indMasDeuda" : "0",
                                            "cantidadDocsDeuda" : len(invoice_ids),
                                            "datosEmpresa" : "",
                                            "listaDocumentos" : {
                                                "documento" : vals
                                            }
                                        }
                                    }
                                }
                            }
                       }

                    else:
                        json_data = json_response("ConsultarDeudaResponse", api_cabecera, "3009", "NO TIENE DEUDAS PENDIENTES")

                else:
                    error_data = "CODIGO DE CONVENIO NO EXISTE!"
                    transaccion_status = "error"
                    json_data = json_response("ConsultarDeudaResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")

            else:
                json_data = json_response("ConsultarDeudaResponse", api_cabecera, "0101", "NUMERO DE REFERENCIA NO EXISTE")

            #Transacción realizada con éxito
            transaccion_status = "done"

        except Exception as e:
            error_data = str(e)
            transaccion_status = "error"

            json_data = json_response("ConsultarDeudaResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")


        event_obj.update({'json_out':json.dumps(json_data, indent=4, sort_keys=True), 'error_details': error_data, 'stages_id' : transaccion_status})


        return successful_response (200, json_data)


    @http.route('/Notificarpago', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_notificar_pago(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        # Get request parameters from body
        values = {}
        try:
            values = json.loads(request.httprequest.stream.read())

            api_cabecera = values['NotificarPago']['recaudosRq']['cabecera']

            api_transaccion = values['NotificarPago']['recaudosRq']['detalle']['transaccion']
            api_referencia = api_transaccion['numeroReferenciaDeuda']
            api_nro_documento = api_transaccion['numeroDocumento']
            api_importe = api_transaccion['importeDeudaPagada']
            api_nro_operacion = api_transaccion['numeroOperacionRecaudos']
            api_formaPago = api_transaccion['formaPago']
            api_codigoMoneda = api_transaccion['codigoMoneda']

            #REGISTO DE LOG
            log_data = {
                "name" : api_cabecera['operacion']['codigoOperacion'],
                "web_service" : "NotificarPago",
                "referencia_deuda" : api_referencia,
                "numero_documento" : api_nro_documento,
                "codigoOperacion" : api_cabecera['operacion']['codigoOperacion'],
                "numeroOperacion" : api_cabecera['operacion']['numeroOperacion'],
                "codigoBanco" : api_cabecera['operacion']['codigoBanco'],
                "codigoConvenio" : api_cabecera['operacion']['codigoConvenio'],
                "canalOperacion" : api_cabecera['operacion']['canalOperacion'],
                "codigoOficina" : api_cabecera['operacion']['codigoOficina'],
                "fechaOperacion" : api_cabecera['operacion']['fechaOperacion'], 
                "horaOperacion" : api_cabecera['operacion']['horaOperacion'],

                "json_in" : json.dumps(values, indent=4, sort_keys=True),
                "company_id" : request.env.user.company_id.id,
                "stages_id" : 'new'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)

        except Exception as e:
            #REGISTO DE LOG DE ERROR
            log_data = {
                "name" : "",
                "web_service" : "NotificarPago",
                "json_in" : str(values),
                "company_id" : request.env.user.company_id.id,
                'error_details': str(e),
                "stages_id" : 'error'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)
            json_data = json_response("NotificarPagoResponse", None, "3000", "FORMATO DE TRAMA NO VÁLIDO")
            return successful_response (200, json_data)


        #EXTRAER DATOS DE CONEXION Y CONFIGURACIÓN
        company = request.env.user.company_id

        asignar_configuracion(company.param_url, company.param_db, company.param_username, company.param_password,
            company.param_currency_usd, company.param_currency_pen, company.param_journal_usd, company.param_journal_pen,
            company.param_account_usd, company.param_account_pen)

        error_data = ""

        try:

            #Conexion con Base de datos
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            uid = common.authenticate(DATABASE, username, password, {})
            #print (common.version())

            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            conex_result = models.execute_kw(DATABASE, uid, password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

            #Buscar el Cliente
            partner = models.execute_kw(DATABASE, uid, password,'res.partner', 'search_read', [[['ref', '=', api_referencia]]],
                {'fields': ['id', 'name'], 'limit': 1})

            if partner:

                partner_id = partner[0]['id']
                partner_name = partner[0]['name']

                #Buscar la factura con saldo del cliente
                #['invoice_payment_state', '=', 'not_paid'],
                invoice_ids = models.execute_kw(DATABASE, uid, password,
                    'account.move', 'search_read',
                    [[['type', '=', 'out_invoice'], 
                        ['state', '=', 'posted'], 
                        ['partner_id', '=', partner_id ],
                        ['ref', '=', api_nro_documento ]]],
                    {'fields': ['id', 'ref', 'glosa', 'invoice_date', 'invoice_date_due', 'amount_residual','invoice_payment_state','currency_id'], 'limit': 1})


                if invoice_ids:

                    payment_state = invoice_ids[0]['invoice_payment_state']
                    if payment_state == "not_paid":

                        if float(api_importe) >= 1 and float(api_importe) <= invoice_ids[0]['amount_residual']: #SOLO SE ACEPTA EL PAGO TOTAL

                            invoice_id = invoice_ids[0]['id']

                            #Codigo de moneda
                            api_currency = GLOBAL_CURRENCY_PEN

                            if api_codigoMoneda == "PEN" :
                                api_currency = GLOBAL_CURRENCY_PEN #ID Moneda Soles
                                api_journal = GLOBAL_JOURNAL_PEN   #ID Diario Soles
                                api_account = GLOBAL_ACCOUNT_PEN   #ID Cta Soles

                            elif api_codigoMoneda == "USD": 
                                api_currency = GLOBAL_CURRENCY_USD #ID Moneda Dolares
                                api_journal = GLOBAL_JOURNAL_USD  #ID Diario Dolares
                                api_account = GLOBAL_ACCOUNT_USD   #ID Cta Dolares

                            if api_currency == int(invoice_ids[0]['currency_id'][0]): #MONEDA DEL PAGO ES IGUAL A MONEDA DE LA FACTURA

                                #Forma de pago
                                if api_formaPago == "EF" :
                                    api_formaPago_id = 9 #009 - EFECTIVO, EN LOS DEMÁS CASOS
                                elif api_formaPago == "CT": 
                                    api_formaPago_id = 1 #001 - DEPÓSITO EN CUENTA
                                elif api_formaPago == "CJ": 
                                    api_formaPago_id = 7 #007 - CHEQUES NO NEGOCIABLES
                                elif api_formaPago == "TC": 
                                    api_formaPago_id = 6 #006 - TARJETA DE CRÉDITO
                                elif api_formaPago == "CP": 
                                    api_formaPago_id = 7 #007 - CHEQUES NO NEGOCIABLES

                                #Tipo de documento
                                api_type_document_id = 1 #00 - Otros

                                if api_nro_documento.startswith("F"):
                                    api_type_document_id = 2 #01 - Factura
                                elif api_nro_documento.startswith("B"): 
                                    api_type_document_id = 4 #03 -  Boleta de Venta
                                
                                #Crear el Pago
                                payment_id = models.execute_kw(DATABASE, uid, password, 'account.payment', 'create', 
                                    [{
                                        'payment_type': 'inbound',
                                        'payment_date': '{}'.format(datetime.now()),
                                        'partner_type':'customer',
                                        'partner_id': partner_id,
                                        'journal_id': api_journal,
                                        'destination_account_id': api_account,
                                        'communication': api_nro_operacion,
                                        'payment_method_id' : 1,
                                        'state':'draft',
                                        'currency_id': api_currency,
                                        'nro_comp' : api_nro_documento,
                                        'cash_nro_comp' : api_nro_operacion,
                                        'catalog_payment_id' : api_formaPago_id,
                                        'type_document_id' : api_type_document_id,
                                        'amount': float(api_importe),
                                        'invoice_ids':[(6,0,[invoice_id])]
                                    }])

                                #Publicar el pago
                                post_result = models.execute_kw(DATABASE, uid, password, 'account.payment', 'post',
                                    [payment_id], {})

                                json_data = {
                                    "NotificarPagoResponse":   {
                                        "recaudosRs" : {
                                            "cabecera" : api_cabecera,
                                            "detalle" : {
                                                "respuesta" : {
                                                    "codigo" : "0001",
                                                    "descripcion" : "TRANSACCION REALIZADA CON EXITO"
                                                },
                                                "transaccion" : {
                                                    "numeroReferenciaDeuda" : api_referencia,
                                                    "numeroOperacionEmpresa" : str(payment_id),
                                                    "datosEmpresa" : False
                                                }
                                            }
                                        }
                                    }
                               }

                            else:
                                error_data = "EL PAGO ESTA EN UNA MONEDA DIFERENTE!"
                                transaccion_status = "error"
                                json_data = json_response("NotificarPagoResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")    

                        else:
                            json_data = json_response("NotificarPagoResponse", api_cabecera, "3051", "MONTO DE PAGO DEBE SER  MINIMO O MAXIMO")

                    else:
                        json_data = json_response("NotificarPagoResponse", api_cabecera, "0106", "NUMERO DE REFERENCIA CON ESTADO PAGADO")

                else:
                    error_data = "DOCUMENTO NO ENCONTRADO!"
                    transaccion_status = "error"
                    json_data = json_response("NotificarPagoResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")

            else:
                json_data = json_response("NotificarPagoResponse", api_cabecera, "0101", "NUMERO DE REFERENCIA NO EXISTE")

            #Transacción realizada con éxito
            transaccion_status = "done"

        except Exception as e:
            error_data = str(e)
            transaccion_status = "error"

            json_data = json_response("NotificarPagoResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")


        event_obj.update({'json_out':json.dumps(json_data, indent=4, sort_keys=True), 'error_details': error_data, 'stages_id' : transaccion_status})


        return successful_response (200, json_data)



    @http.route('/ExtornarPago', type='http', methods=['POST'], csrf=False, auth="public", cors='*')
    def api_extornar_pago(self, **args):

        args = json.loads(json.dumps(request.httprequest.args))
        # Get request parameters from body
        values = {}
        try:
            values = json.loads(request.httprequest.stream.read())

            api_cabecera = values['ExtornarPago']['recaudosRq']['cabecera']

            api_transaccion = values['ExtornarPago']['recaudosRq']['detalle']['transaccion']
            api_referencia = api_transaccion['numeroReferenciaDeuda']
            api_nro_documento = api_transaccion['numeroDocumento']
            api_importe = api_transaccion['importeDeudaPagada']
            api_nro_operacion = api_transaccion['numeroOperacionRecaudos']
            api_formaPago = api_transaccion['formaPago']
            api_codigoMoneda = api_transaccion['codigoMoneda']

            #REGISTO DE LOG
            log_data = {
                "name" : api_cabecera['operacion']['codigoOperacion'],
                "web_service" : "ExtornarPago",
                "referencia_deuda" : api_referencia,
                "numero_documento" : api_nro_documento,
                "codigoOperacion" : api_cabecera['operacion']['codigoOperacion'],
                "numeroOperacion" : api_cabecera['operacion']['numeroOperacion'],
                "codigoBanco" : api_cabecera['operacion']['codigoBanco'],
                "codigoConvenio" : api_cabecera['operacion']['codigoConvenio'],
                "canalOperacion" : api_cabecera['operacion']['canalOperacion'],
                "codigoOficina" : api_cabecera['operacion']['codigoOficina'],
                "fechaOperacion" : api_cabecera['operacion']['fechaOperacion'], 
                "horaOperacion" : api_cabecera['operacion']['horaOperacion'],

                "json_in" : json.dumps(values, indent=4, sort_keys=True),
                "company_id" : request.env.user.company_id.id,
                "stages_id" : 'new'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)

        except Exception as e:
            #REGISTO DE LOG DE ERROR
            log_data = {
                "name" : "",
                "web_service" : "ExtornarPago",
                "json_in" : str(values),
                "company_id" : request.env.user.company_id.id,
                'error_details': str(e),
                "stages_id" : 'error'
                }
            
            event_obj = request.env['logs.request'].sudo().create(log_data)
            json_data = json_response("ExtornarPagoResponse", None, "3000", "FORMATO DE TRAMA NO VÁLIDO")
            return successful_response (200, json_data)

        #EXTRAER DATOS DE CONEXION Y CONFIGURACIÓN
        company = request.env.user.company_id

        asignar_configuracion(company.param_url, company.param_db, company.param_username, company.param_password,
            company.param_currency_usd, company.param_currency_pen, company.param_journal_usd, company.param_journal_pen,
            company.param_account_usd, company.param_account_pen)

        error_data = ""

        try:

            #Conexion con Base de datos
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            uid = common.authenticate(DATABASE, username, password, {})
            #print (common.version())

            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(URL),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            conex_result = models.execute_kw(DATABASE, uid, password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

            #Buscar el Cliente
            partner = models.execute_kw(DATABASE, uid, password,'res.partner', 'search_read', [[['ref', '=', api_referencia]]],
                {'fields': ['id', 'name'], 'limit': 1})

            if partner:

                partner_id = partner[0]['id']
                partner_name = partner[0]['name']

                #Buscar el pago
                payment_ids = models.execute_kw(DATABASE, uid, password,
                    'account.payment', 'search_read',
                    [[['payment_type', '=', 'inbound'], 
                        ['state', '=', 'posted'], 
                        ['partner_type', '=', 'customer'],
                        ['amount', '=', float(api_importe)],
                        ['partner_id', '=', partner_id ],
                        ['nro_comp', '=', api_nro_documento ]]],
                    {'fields': ['id', 'name', 'state'], 'limit': 1})

                if payment_ids:

                    payment_id = payment_ids[0]['id']

                    #Cambiar a borrador el pago
                    action_draft_result = False
                    try:
                        action_draft_result = models.execute_kw(DATABASE, uid, password, 'account.payment', 'action_draft', [payment_id], {})
                    except:
                        action_draft_result = "X AL LLAMAR action_draft"


                    #Cancelar a borrador el pago
                    cancel_result = False
                    try:
                        cancel_result = models.execute_kw(DATABASE, uid, password, 'account.payment', 'cancel', [payment_id], {})
                    except:
                        cancel_result = "X AL LLAMAR cancel"

                    json_data = {
                        "ExtornarPagoResponse":   {
                            "recaudosRs" : {
                                "cabecera" : api_cabecera,
                                "detalle" : {
                                    "respuesta" : {
                                        "codigo" : "0001",
                                        "descripcion" : "TRANSACCION REALIZADA CON EXITO"
                                    },
                                    "transaccion" : {
                                        "numeroReferenciaDeuda" : api_referencia,
                                        "numeroOperacionEmpresa" : str(payment_id),
                                        "datosEmpresa" : False
                                    }
                                }
                            }
                        }
                   }

                else:
                    json_data = json_response("ExtornarPagoResponse", api_cabecera, "3014", "EXTORNO NO PROCESADO PORQUE NO EXISTE REGISTRO DEL PAGO")

            else:
                json_data = json_response("ExtornarPagoResponse", api_cabecera, "0101", "NUMERO DE REFERENCIA NO EXISTE")

            #Transacción realizada con éxito
            transaccion_status = "done"

        except Exception as e:
            error_data = str(e)
            transaccion_status = "error"

            json_data = json_response("ExtornarPagoResponse", api_cabecera, "3002", "NO SE PUDO REALIZAR LA TRANSACCIÓN")

        event_obj.update({'json_out':json.dumps(json_data, indent=4, sort_keys=True), 'error_details': error_data, 'stages_id' : transaccion_status})

        return successful_response (200, json_data)
