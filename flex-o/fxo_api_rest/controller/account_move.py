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
# /api/v1/account_move/<id>             GET     - Read one
# /api/v1/account_move                  POST    - Create one
# /api/v1/account_move/<id>             PUT     - Update one
# /api/v1/account_move/<id>             DELETE  - Delete one

class ApiAccountMove(http.Controller):
    MANDATORY_FIELDS    =    ["name","type"]
    RELATIONAL_FIELDS   =    ["partner_id","currency_id","company_id","diario_move_detraccion","invoice_payment_term_id","op_type_sunat_id",
                                "type_document_id","user_id"]

    OPTIONAL_FIELDS     =   ["id","invoice_origin","glosa","ref","currency_rate","amount_residual","amount_residual_signed","amount_tax",
                            "amount_tax_signed","amount_total","amount_total_signed",
                            "amount_untaxed","amount_untaxed_signed","detra_amount","type_invoice"
                            "detraction_amount","doc_origin_customer","hash_code","is_descount","number_perception","state",
                            "sunat_state","type_t_perception","invoice_payment_state","corporate_reference","shipping_documents"
                            ]
    OPTIONAL_DATE       =  ["date_detraccion","fecha_move_detraccion","invoice_date","invoice_date_due","perception_date"]

    def log_api_registro(self,codigo,tipo_solicitud,json_in,json_out,error_details,company_id,state):
        data  = {
                    'name': True,
                    'web_service': '/api/v1/account_move/',
                    'codigo':codigo,
                    'tipo_solicitud':tipo_solicitud,
                    'modelo': 'Factura de Cliente',
                    'json_in':json_in,
                    'json_out':json_out,
                    'error_details':error_details,
                    'company_id':company_id,
                    'state':state
                }
        log_api = http.request.env['api.logs.request'].sudo().create([data])

    def data_return_account_move(self,move):
        values = {key: move[key] for key in self.MANDATORY_FIELDS }
        values.update({key:int( move[key]['id']) for key in self.RELATIONAL_FIELDS })
        values.update({key: move[key] for key in self.OPTIONAL_FIELDS if key in move})
        line = []
        for item in move.invoice_line_ids:
            dato = {
                'id':item.id,
                'name':item.name,
                'product_id': item.product_id.id,
                'price_subtotal': item.price_subtotal,
                'id_loges' : item.id_loges
            }
            line.append(dato)
        values.update({'invoice_line_ids':line})

        return values
    
    def return_success(self,move):
        data = self.data_return_account_move(move)
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
            'error_mensaje': err if  err else err
        }
        _logger.error("%s", err)
        #self.log_api_registro('400',metodo,str(kw),str(data),err,'','error')
        return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
    
    @http.route('/api/v1/account_move/', type='http', auth="public", methods=['POST'],csrf=False)
    def api_account_move_post(self, *args, **kw):
        try:
            values = {key: kw[key] for key in self.MANDATORY_FIELDS}
            values.update({key: kw[key] for key in self.RELATIONAL_FIELDS if key in kw })
            values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
            values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})

            l10n_latam_identification_type = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('l10n_latam_identification_type_id'))])
            if len(l10n_latam_identification_type)==1:
                tipo_documento = l10n_latam_identification_type[0].id
            else :
                return self.erro_success("Tipo de Documento no encontrado",kw,'POST')
            
            print("Data ")
            print(kw.get('bill_to_typedocument_inv'))
            print(kw.get('bill_to_numberdocument_inv'))
            
            bill_to_typedocument_inv = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('bill_to_typedocument'))])
            if len(bill_to_typedocument_inv)==1:
                bill_to_typedocument_inv = bill_to_typedocument_inv[0].id
                bill_to_numberdocument_inv = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('bill_to_numberdocument')) ,('l10n_latam_identification_type_id','=',bill_to_typedocument_inv)])
        
            else :
                bill_to_typedocument_inv = False
                bill_to_numberdocument_inv = False


            partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id')) ,('l10n_latam_identification_type_id','=',tipo_documento)])

            if len(partner) > 0:
                values.update({'partner_id':partner[0].id})
            else :
                return self.erro_success("Partner No encontrado",kw,'POST')

            company  =  http.request.env['res.company'].sudo().search([('id', '=', int(kw.get('company_id'))) ])

            if len(company) ==  0 :
                return self.erro_success("Compania no emcontrada",kw,'POST')

            currency = http.request.env['res.currency'].sudo().search([('name', '=', kw.get('currency_id'))])
            if len(currency) > 0:
                values.update({'currency_id':currency[0].id})
            else:
                return self.erro_success("Moneda No Encontrada",kw,'POST')

            journal = http.request.env['account.journal'].sudo().search([('code', '=', kw.get('journal_id')), ('company_id','=',company.id )])
            if len(journal) > 0:
                values.update({'journal_id':journal[0].id})
            else:
                return self.erro_success(" Diario No Encontrado",kw,'POST')
            
            #serie = http.request.env['it.invoice.serie'].sudo().search([('name', '=', kw.get('serie_id')), ('company_id','=',company.id )])
            #if len(serie) > 0:
            #    values.update({'serie_id':serie[0].id})

#            serie = http.request.env['it.invoice.serie'].sudo().search([('name', '=', kw.get('serie_id')), ('company_id','=',company.id )])
#            if len(serie) > 0:
#                values.update({'serie_id':serie[0].id})

            type_document_id = http.request.env['einvoice.catalog.01'].sudo().search([('code', '=', kw.get('type_document_id'))])
            if len(type_document_id) > 0:
                values.update({'type_document_id':type_document_id[0].id})
            else:
                return self.erro_success(" Tipo de Documento No Encontrado",kw,'POST')
            
            user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('user_id'))])
            if len(user)==1:
                values.update({'user_id':user.id})
            #else:
            #    return self.erro_success(" Usuario No Encontrado")
            
            # SFR estaba comentado
            property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', kw.get('invoice_payment_term_id'))])
            
            if len(property_payment_term)==1:
                values.update({'invoice_payment_term_id':property_payment_term.id})
            else:
                return self.erro_success(" Termino de pago Encontrado",kw,'POST')

            op_type_sunat_id =  http.request.env['einvoice.catalog.51'].sudo().search([('code', '=', kw.get('op_type_sunat_id'))])
            if len(op_type_sunat_id)==1:
                values.update({'op_type_sunat_id':op_type_sunat_id.id})
            else :
                values.update({'op_type_sunat_id':0})
            
            debit_note_type_id  =  http.request.env['einvoice.catalog.10'].sudo().search([('code', '=', kw.get('debit_note_type_id'))])
            if len(debit_note_type_id)==1:
                values.update({'debit_note_type_id':debit_note_type_id.id})
            
            credit_note_type_id =  http.request.env['einvoice.catalog.09'].sudo().search([('code', '=', kw.get('credit_note_type_id'))])
            if len(credit_note_type_id)==1:
                values.update({'credit_note_type_id':credit_note_type_id.id})
            

            invoice_incoterm_id =  http.request.env['account.incoterms'].sudo().search([('code', '=', kw.get('invoice_incoterm_id'))])
            if len(invoice_incoterm_id)==1:
                values.update({'invoice_incoterm_id':invoice_incoterm_id.id})
            
            tipo_documento_user = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('import_sales_executive_type_document') )])
            if len(tipo_documento_user)==1:
                tipo_documento_user = tipo_documento_user[0].id
                user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('import_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',tipo_documento_user)])
                if len(user) > 0:
                    values.update({'invoice_user_id':user[0].id})
            
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

            # lineas de factura
            invoice_line_ids =[]
            texto = kw.get('invoice_line_ids')
            line_ids =  json.loads(texto)

            for item in line_ids:
                temp = {
                    'name' :            item['name'],
                    'quantity':         item['quantity'],
                    'price_unit':       item['price_unit'],
                    'price_subtotal':   item['price_subtotal'],
                    'nro_comp' :        item['nro_comp'],
                    'id_loges' :        item['id_loges'],
                }
                #account_id = http.request.env['account.account'].sudo().search([('code', '=',item['account_id']),('company_id','=',int(kw.get('company_id') ) )])
                #if len(account_id) > 0:
                #    temp.update({'account_id':account_id[0].id})
                
                bill_to_typedocument = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', item['supplier_type_document'])])
                if len(bill_to_typedocument)==1:
                    bill_to_typedocument = bill_to_typedocument[0].id
                    bill_to_numberdocument = http.request.env['res.partner'].sudo().search([('vat', '=', item['supplier_number_document']) ,('l10n_latam_identification_type_id','=',bill_to_typedocument)])
                    if len(bill_to_numberdocument) > 0: 
                        temp.update({'partner_id':bill_to_numberdocument[0].id})

                analytic_account_id = http.request.env['account.analytic.account'].sudo().search([('code', '=', item['analytic_account_id']  ),('company_id','=',int(kw.get('company_id') )) ])
                if len(analytic_account_id) > 0:
                    temp.update({'analytic_account_id':analytic_account_id[0].id})

                product_id = http.request.env['product.product'].sudo().search([('default_code', '=',  item['product_id'])])
                if len(product_id) > 0:
                    temp.update({'product_id':product_id[0].id})
                else :
                    return self.erro_success("Producto No encontrado" + "con el codigo " + item['product_id'],kw,'POST') 
               # if product_id.property_account_income_id.id :
               #     pass
               # else :
               #     return self.erro_success("Producto  no tiene cuenta contable " + "con el codigo " + item['product_id'],kw,'POST')

                product_uom_id  = http.request.env['uom.uom'].sudo().search([('name', '=', kw.get('product_uom_id') )])
                if len(product_uom_id) > 0:
                    temp.update({'product_uom_id':product_uom_id[0].id})
                
                
                if journal.is_liquidation_refundable == False:
                    tax_ids = http.request.env['account.tax'].sudo().search([('l10n_pe_edi_tax_code', '=',item['tax_ids'] ) ,('type_tax_use','=','sale') ,('company_id','=',int(kw.get('company_id') ) )   ])
                    if len(tax_ids) > 0:
                        temp.update({'tax_ids': [(6, 0, tax_ids.ids)]})
                    else :
                        return self.erro_success("Impuesto No encontrado",kw,'POST' ) 

                order_id  = http.request.env['sale.order'].sudo().search([('name', '=',item['order_id'] )])
                if len(order_id) > 0:
                    temp.update({'order_id': order_id.id})
                invoice_line_ids.append(temp)

            # Linea factura
            account_cant = http.request.env['account.move'].sudo().search([('name', '=', kw.get('name')),('company_id','=',int(values.get('company_id') ) )])
            if len(account_cant) > 0:
                #return self.erro_success("Factura ya Registrado")
                return self.return_success(account_cant)
            else :
                inv = {
                        #"name": str(kw.get('name')), 
                        "type": str(kw.get('type')), 
                        "partner_id": partner[0].id, 
                        "currency_id": currency[0].id, 
                        "company_id": int(values.get('company_id') ), 
                        "diario_move_detraccion": 0, 
                        "invoice_payment_term_id": property_payment_term.id if property_payment_term.id else 1, 
                        "op_type_sunat_id": op_type_sunat_id[0].id if len(op_type_sunat_id) > 0 else False , 
                        "type_document_id": type_document_id[0].id if len(type_document_id) > 0 else False, 
                        "invoice_origin": str(values.get('invoice_origin')), 
                        "glosa": str(values.get('glosa')), 
                        "ref": str(values.get('ref')),
                        "currency_rate": float(values.get('currency_rate')),
                        "amount_residual": float(values.get('amount_residual')), 
                        "amount_residual_signed": float(values.get('amount_residual_signed')),
                        "amount_tax": float(values.get('amount_tax')), 
                        "amount_tax_signed": float(values.get('amount_tax_signed')), 
                        "amount_total": float(values.get('amount_total')), 
                        "amount_total_signed": float(values.get('amount_total_signed')),
                        "amount_untaxed": float(values.get('amount_untaxed')), 
                        "amount_untaxed_signed": float(values.get('amount_untaxed_signed')),
                        "detra_amount": float(values.get('detra_amount')), 
                       # "detraction_amount": float(values.get('detraction_amount')),
                        "doc_origin_customer": str(values.get('doc_origin_customer')), 
                        "hash_code": str(values.get('hash_code')),
                        "journal_id": int(values.get('journal_id')),
                        "bill_to_typedocument":bill_to_numberdocument_inv,
                        "bill_to_numberdocument":bill_to_numberdocument_inv,
                        "state": "draft", 
                        "sunat_state": "0",
                        "invoice_date": values.get('invoice_date'),
                        "invoice_user_id" :values.get('invoice_user_id'),
                        "invoice_expo_user_id" :values.get('invoice_expo_user_id'),
                        "collection_id" :values.get('collection_id'),
                        "corporate_reference": values.get('corporate_reference'),
                        "shipping_documents":values.get('shipping_documents'),
                        "tc_per" : True,
                        "invoice_line_ids": []
                    }
                for  item in invoice_line_ids:
                    inv['invoice_line_ids'].append((0, 0, item))
                
                account_cant = http.request.env['account.move'].sudo().search([('ref', '=', kw.get('ref')), ('type', '=', kw.get('type')), ('company_id','=',int(values.get('company_id') ) )])
                
                if len(account_cant) == 0:
                    print(inv)
                    account_move = http.request.env['account.move'].sudo().create(inv)
                    
                    account_move.amount_residual = account_move.amount_total
                    account_move.amount_residual_signed = account_move.amount_total_signed

                    account_move.sudo().action_post()
                    for item in line_ids:           
                        move_line = http.request.env['account.move.line'].sudo().search([('id_loges', '=', item['id_loges']), ('company_id','=',int(values.get('company_id') ) )])
                        move_line.nro_comp = item['nro_comp'] 
                        bill_to_typedocument = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', item['supplier_type_document'])])
                        if len(bill_to_typedocument) == 1:
                            bill_to_typedocument = bill_to_typedocument[0].id
                            bill_to_numberdocument = http.request.env['res.partner'].sudo().search([('vat', '=', item['supplier_number_document']) ,('l10n_latam_identification_type_id','=',bill_to_typedocument)])
                            if len(bill_to_numberdocument) > 0:
                                move_line.partner_id =  bill_to_numberdocument[0].id

                    self.log_api_registro('200','POST',str(kw),str(inv),'',int(values.get('company_id')),'done')
                    return self.return_success(account_move)
                return self.return_success(account_cant)
        except Exception as err:
            account_cant = http.request.env['account.move'].sudo().search([('ref', '=', kw.get('ref')), ('type', '=', kw.get('type')), ('company_id','=',int(values.get('company_id') ) )])
            if len(account_cant) == 1:
                account_cant.unlink()
            return self.erro_success(err.args,kw,'POST') 
    
    @http.route('/api/v1/account_move/<string:ids>/<string:company_id>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_account_move_put(self,ids=None,company_id=None ,*args,**kw):
        account_move = http.request.env['account.move'].sudo().search([('name', '=', ids),('company_id','=',int(company_id))])

        if len(account_move) > 0:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS}
                values.update({key:kw[key] for key in self.RELATIONAL_FIELDS if key in kw })
                values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
                values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})
                
                partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id'))])
                if len(partner) > 0:
                    values.update({'partner_id':partner[0].id})
                else :
                    values.pop('partner_id')

                currency = http.request.env['res.currency'].sudo().search([('name', '=', kw.get('currency_id'))])
                if len(currency) > 0:
                    values.update({'currency_id':currency[0].id})
                else :
                    values.pop('currency_id')


                journal = http.request.env['account.journal'].sudo().search([('code', '=', kw.get('journal_id')), ('company_id','=',int(company_id))])
                if len(journal) > 0:
                    values.update({'journal_id':journal[0].id})
                else :
                    values.pop('journal_id')


                type_document_id = http.request.env['einvoice.catalog.01'].sudo().search([('code', '=', kw.get('type_document_id'))])
                if len(type_document_id) > 0:
                    values.update({'type_document_id':type_document_id[0].id})
                else :
                    values.pop('type_document_id')

                user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('user_id'))])
                if len(user)==1:
                    values.update({'user_id':user.id})
                else :
                    values.pop('user_id')
                
                property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', kw.get('invoice_payment_term_id'))])
                
                if len(property_payment_term)==1:
                    values.update({'invoice_payment_term_id':property_payment_term.id})
                else :
                    values.pop('invoice_payment_term_id')

                op_type_sunat_id =  http.request.env['einvoice.catalog.51'].sudo().search([('code', '=', kw.get('op_type_sunat_id'))])
                if len(op_type_sunat_id)==1:
                    values.update({'op_type_sunat_id':op_type_sunat_id.id})
                else :
                    values.pop('op_type_sunat_id')
                
                debit_note_type_id  =  http.request.env['einvoice.catalog.10'].sudo().search([('code', '=', kw.get('debit_note_type_id'))])
                if len(debit_note_type_id)==1:
                    values.update({'debit_note_type_id':debit_note_type_id.id})

                
                credit_note_type_id =  http.request.env['einvoice.catalog.09'].sudo().search([('code', '=', kw.get('credit_note_type_id'))])
                if len(credit_note_type_id)==1:
                    values.update({'credit_note_type_id':debit_note_type_id.id})


                invoice_incoterm_id =  http.request.env['account.incoterms'].sudo().search([('code', '=', kw.get('invoice_incoterm_id'))])
                if len(invoice_incoterm_id)==1:
                    values.update({'invoice_incoterm_id':invoice_incoterm_id.id})


                
                account_move[0].sudo().write(values)

                return self.return_success(account_move)
            except Exception as err:
                return self.erro_success(err.args,kw,'PUT') 
        else:
            return self.erro_success('No Encontrado',kw,'PUT')

    @http.route('/api/v1/account_move/<string:ids>/<string:company_id>', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_account_move_gets(self, ids=None,company_id=None , **get):
        account_move = http.request.env['account.move'].sudo().search([('name', '=', ids),('company_id','=',int(company_id))])
        if len(account_move)>0:
            return self.return_success(account_move)
        else :
            return self.erro_success('error','','GET')
        
    @http.route('/api/v1/account_move/<string:ids>/<string:company_id>', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_account_move_delete(self, ids=None,company_id=None , *args, **kw):
        account_move = http.request.env['account.move'].sudo().search([('name', '=', ids),('company_id','=',int(company_id))])
        data = {}
        if len(account_move) == 1:
            try:
                account_move.unlink()
                data = {
                'success': True,
                'status_code': 200,
                }
                return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
            except Exception as err:
                
                return self.erro_success(err.args,kw,'delete')
        else :
            data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
    @http.route('/api/v1/account_move/<int:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_account_move_put_id(self,ids=None,company_id=None ,*args,**kw):
        account_move = http.request.env['account.move'].sudo().search([('id', '=', ids)])

        if len(account_move) > 0:
            try:
                values = {key: kw[key] for key in self.MANDATORY_FIELDS}
                values.update({key:kw[key] for key in self.RELATIONAL_FIELDS if key in kw })
                values.update({key: kw[key] for key in self.OPTIONAL_FIELDS if key in kw})
                values.update({key: kw[key] for key in self.OPTIONAL_DATE if key in kw})
                
                partner = http.request.env['res.partner'].sudo().search([('vat', '=', kw.get('partner_id'))])
                if len(partner) > 0:
                    values.update({'partner_id':partner[0].id})
                else :
                    values.pop('partner_id')

                currency = http.request.env['res.currency'].sudo().search([('name', '=', kw.get('currency_id'))])
                if len(currency) > 0:
                    values.update({'currency_id':currency[0].id})
                else :
                    values.pop('currency_id')


                journal = http.request.env['account.journal'].sudo().search([('code', '=', kw.get('journal_id')), ('company_id','=',int(company_id))])
                if len(journal) > 0:
                    values.update({'journal_id':journal[0].id})
                else :
                    values.pop('journal_id')


                type_document_id = http.request.env['einvoice.catalog.01'].sudo().search([('code', '=', kw.get('type_document_id'))])
                if len(type_document_id) > 0:
                    values.update({'type_document_id':type_document_id[0].id})
                else :
                    values.pop('type_document_id')

                user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('user_id'))])
                if len(user)==1:
                    values.update({'user_id':user.id})
                else :
                    values.pop('user_id')
                
                property_payment_term = http.request.env['account.payment.term'].sudo().search([('code', '=', kw.get('invoice_payment_term_id'))])
                
                if len(property_payment_term)==1:
                    values.update({'invoice_payment_term_id':property_payment_term.id})
                else :
                    values.pop('invoice_payment_term_id')

                op_type_sunat_id =  http.request.env['einvoice.catalog.51'].sudo().search([('code', '=', kw.get('op_type_sunat_id'))])
                if len(op_type_sunat_id)==1:
                    values.update({'op_type_sunat_id':op_type_sunat_id.id})
                else :
                    values.pop('op_type_sunat_id')
                
                debit_note_type_id  =  http.request.env['einvoice.catalog.10'].sudo().search([('code', '=', kw.get('debit_note_type_id'))])
                if len(debit_note_type_id)==1:
                    values.update({'debit_note_type_id':debit_note_type_id.id})

                
                credit_note_type_id =  http.request.env['einvoice.catalog.09'].sudo().search([('code', '=', kw.get('credit_note_type_id'))])
                if len(credit_note_type_id)==1:
                    values.update({'credit_note_type_id':debit_note_type_id.id})


                invoice_incoterm_id =  http.request.env['account.incoterms'].sudo().search([('code', '=', kw.get('invoice_incoterm_id'))])
                if len(invoice_incoterm_id)==1:
                    values.update({'invoice_incoterm_id':invoice_incoterm_id.id})
                
                tipo_documento_user = http.request.env['l10n_latam.identification.type'].sudo().search([('code_sunat', '=', kw.get('import_sales_executive_type_document') )])
                if len(tipo_documento_user)==1:
                    tipo_documento_user = tipo_documento_user[0].id
                    user = http.request.env['res.users'].sudo().search([('vat', '=', kw.get('import_sales_executive_number_document')) ,('l10n_latam_identification_type_id','=',tipo_documento_user)])
                    if len(user) > 0:
                        values.update({'invoice_user_id':user[0].id})
                
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

                
                account_move[0].sudo().write(values)

                return self.return_success(account_move)
            except Exception as err:
                return self.erro_success(err.args,kw,'PUT') 
        else:
            return self.erro_success('No Encontrado',kw,'PUT') 

    @http.route('/api/v1/account_move/<int:ids>/', type='http', auth="public", methods=['get'], website=True,csrf=False)
    def api_account_move_gets_id(self, ids=None,company_id=None , **get):
        account_move = http.request.env['account.move'].sudo().search([('id', '=', ids)])
        if len(account_move)>0:
            return self.return_success(account_move)
        else :
            return self.erro_success('No Encontrado',get,'PUT')
        
    @http.route('/api/v1/account_move/<int:ids>/', type='http', auth="public", methods=['delete'], website=True,csrf=False)
    def api_account_move_delete_id(self, ids=None,company_id=None , *args, **kw):
        account_move = http.request.env['account.move'].sudo().search([('id', '=', ids)])
        data = {}
        if len(account_move) == 1:
            try:
                account_move.unlink()
                data = {
                'success': True,
                'status_code': 200,
                }
                return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=200)
            except Exception as err:
                return self.erro_success(err.args,kw,'PUT')
        else :
            data = {'error': True ,'error_mensaje': 'No Encontrado ','status_code': 400}
            return http.Response(json.dumps(data),content_type='application/json;charset=utf-8',status=400)
   
    @http.route('/api/v1/account_move/anular/<int:ids>', type='http', auth="public", methods=['PUT'],csrf=False)
    def api_account_move_line_annul(self,ids=None, *args, **kw):
        account_move = http.request.env['account.move'].sudo().search([('id', '=', ids)])
        if len(account_move) > 0:
            try:
                account_move[0].sudo().button_annul()
                return self.return_success(account_move)
            except Exception as err:
                return self.erro_success(err.args,kw,'PUT')
        else:
            return self.erro_success('No Encontrado',kw,'PUT')