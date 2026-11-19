# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from werkzeug import urls
import os, hashlib, decimal, datetime, re, json, math, sys
import mercadopago
import werkzeug
import time
import logging
_logger = logging.getLogger(__name__)

#./odoo-bin -u mercadopago -c /etc/odoov13-server.conf -d odoov13 --stop-after-init --dev all --dev reload

class payu_controller(http.Controller):
    formsPath = str(os.path.dirname(os.path.abspath(__file__))).replace("controllers","")
    default_documents_types = {"CO":"CC","AR":"DNI","BR":"CPF","CL":"RUT","PE":"DNI","UY":"CI","MX":"RFC"}

    @http.route('/mercadopago/get_mercadopago_acquirer/', methods=['POST'], type='json', auth="public", website=True)
    def get_mercadopago_acquirer(self, **kw):       
        response = {"acquirer":None,"form_bill":None}                
        query = "select name, website_id,company_id, state, provider, mp_service_mode, mp_client_id, mp_client_secret, mp_public_key, mp_access_token, mp_country from payment_acquirer where provider = 'mercadopago' limit 1"
        request.cr.execute(query)    
        acquirer = request.cr.dictfetchone()        
        response = {"acquirer":acquirer,'bill_form': self.file_get_contents(str(self.formsPath)+str("/static/src/form/bill.html")), }
        return response 
    
        
    @http.route('/mercadopago/get_sale_order/', methods=['POST'], type='json', auth="public", website=True)
    def get_sale_order(self, **kw): 
        params = {}
        params['acquirer_id'] = kw.get('acquirer_id')
        params['partner_id'] = kw.get('partner_id')
                       
        query = "select name, website_id,company_id, state, provider, mp_service_mode, mp_client_id, mp_client_secret, mp_public_key, mp_access_token, mp_country from payment_acquirer where provider = 'mercadopago' limit 1"
        
        request.cr.execute(query)
        acquirer = request.cr.dictfetchone()
         
        if(acquirer['state']=="test"):
            state = str('1')
        else:
            state = str('0')

        query = "select id, name, amount_total, amount_tax, date_order, partner_shipping_id from sale_order where partner_id = '"+str(params['partner_id'])+"' and state = '"+str('draft')+"' order by date_order desc limit 1"
        
        request.cr.execute(query)    
        draft_order = request.cr.dictfetchone() 

                  
       
        query = "select res_partner.id, res_partner.name, res_partner.vat, res_partner.phone, res_partner.mobile, res_partner.email, res_partner.street, res_partner.city, res_partner.zip, res_partner.lang, res_country.name as country_name, res_country.code as country_code, res_country_state.name as state_name, res_currency.name as currency_name, res_currency.symbol as currency_symbol from res_partner left join res_country on res_country.id = res_partner.country_id left join res_country_state on res_country_state.id = res_partner.state_id left join res_currency on res_country.currency_id = res_currency.id   where res_partner.id = '"+str(draft_order['partner_shipping_id'])+"' limit 1"
        
        request.cr.execute(query)    
        res_partner_shipping = request.cr.dictfetchone()

        if(draft_order):                                   
            order_name = str(datetime.datetime.now())
            order_name = re.sub('[^0-9]','', order_name)
            order_name = order_name[-9:]

            # base url
            query = "select value from ir_config_parameter where key = 'web.base.url' limit 1"
            request.cr.execute(query)
            ir_config_parameter = request.cr.dictfetchone()
            base_url = ir_config_parameter['value']

            draft_order_lines = http.request.env['sale.order.line'].sudo().search([['order_id','=',draft_order["id"]]])   
            checkout_items = []
            checkout_taxes = []
             
            query = "select show_line_subtotals_tax_selection from res_config_settings where company_id = " + str(request.website.company_id.id)
            request.cr.execute(query)
            setting = request.cr.dictfetchone()

            for order_line in draft_order_lines:
                unit_price = float(0.0)
                
                if(setting):
                    if(setting['show_line_subtotals_tax_selection'] == 'tax_excluded'):
                        if(order_line.currency_id.name=="COP"):
                            unit_price = int(math.ceil(((float(order_line.price_unit) + (float(order_line.price_tax) / float(order_line.product_uom_qty))))))
                        else:
                            unit_price = ((float(order_line.price_unit) + (float(order_line.price_tax) / float(order_line.product_uom_qty)))) # / float(order_line.product_uom_qty)
                            unit_price_parted = str(unit_price).split(".")
                            if(unit_price_parted[1]=="0"):
                                unit_price = unit_price + float(0.01)
                    else:
                        if(order_line.currency_id.name=="COP"):
                            unit_price = int(math.ceil(float(order_line.price_total) / float(order_line.product_uom_qty)))
                        else:
                            unit_price = float(order_line.price_total) / float(order_line.product_uom_qty)
                            unit_price_parted = str(unit_price).split(".")
                            if(unit_price_parted[1]=="0"):
                                unit_price = unit_price + float(0.01)
                        
                checkout_item = {
                                    "title":order_line.name,
                                    "quantity":order_line.product_uom_qty,
                                    "currency_id":order_line.currency_id.name,
                                    "unit_price":unit_price                                    
                                }

                   

                checkout_items.append(checkout_item)
                #product_taxes = http.request.env['product.taxes.rel'].sudo().search([['prod_id','=',order_line.product_id.id]])
                query = "select tax_id from product_taxes_rel where prod_id = " + str(order_line.product_id.id)
                request.cr.execute(query)
                product_taxes = request.cr.dictfetchall()

                if(setting):
                    if(setting['show_line_subtotals_tax_selection'] != 'tax_excluded'):
                        for product_tax in product_taxes:
                            taxes_details = http.request.env['account.tax'].sudo().search([['id','=',product_tax['tax_id']]])  
                            if('IVA' in str(taxes_details.name) and 'INC' in str(taxes_details.name)):
                                if(int(taxes_details.amount)>0):
                                    tax = {"type":"IVA","value":int(taxes_details.amount)}
                                    if(checkout_taxes.__len__()>0):
                                        for tax_added in checkout_taxes:                            
                                            if(int(tax_added["value"])!=int(taxes_details.amount)):
                                                checkout_taxes.append(tax)
                                    else:
                                        checkout_taxes.append(tax)      

            _logger.warning("checkout_item") 
            _logger.warning(setting)
            _logger.warning(checkout_item)                           
            _logger.warning(checkout_taxes)    
            
            jsonPreference = str("")
            if(acquirer['mp_service_mode']=="basic"):
                mp = mercadopago.MP(acquirer['mp_client_id'], acquirer['mp_client_secret'])
                if(state=="1"):
                    mp.sandbox_mode(True)
                else:
                    mp.sandbox_mode(False)

                preference =   {
                                    "items": checkout_items
                               }
                
                

                if(checkout_taxes.__len__()>0):
                    preference['taxes'] = checkout_taxes
                
                if(res_partner_shipping['name']!=""):
                    payer = {
                                "name": res_partner_shipping['name'],
                                "email": res_partner_shipping['email'],
                                "phone": {
                                            "number": res_partner_shipping['phone'] if res_partner_shipping['phone']!="" else res_partner_shipping['mobile']
                                        },
                                "identification":  {
                                                        "type": self.default_documents_types[""+res_partner_shipping['country_code']+""],
                                                        "number": res_partner_shipping['vat']
                                                    },
                                "address": {
                                                "street_name": res_partner_shipping['street'],
                                                "zip_code": res_partner_shipping['zip']
                                            }
                            }
                    preference['payer'] = payer

                    shipments = {
                                    "receiver_address": {
                                                            "zip_code": res_partner_shipping['zip'],
                                                            "street_name": res_partner_shipping['street']
                                                        }
                                }
                    preference['shipments'] = shipments
                
                back_urls = {
                                "success": urls.url_join(base_url, '/shop/process_mercadopago_payment'),
                                "pending": urls.url_join(base_url, '/shop/process_mercadopago_payment'),
                                "failure": urls.url_join(base_url, '/shop/process_mercadopago_payment')
                            }
                preference['back_urls'] = back_urls
                preference['auto_return'] = "approved"
                preference['external_reference'] = draft_order['id']                
                     
                preferenceResult = mp.create_preference(preference)                
                jsonPreference = json.dumps(preferenceResult)
            
            return {
                        'status' :  "OK",
                        'state':state,                        
                        'json_preference':jsonPreference,
                        'checkout_items':checkout_items
                    }

    @http.route('/shop/process_mercadopago_payment', csrf=False, auth="public", website=True)    
    def process_mercadopago_payment(self, **kw):
        _response = {}
       
        _response['collection_id'] = kw.get('collection_id')
        _response['collection_status'] = kw.get('collection_status')
        _response['external_reference'] = kw.get('external_reference')
        _response['payment_type'] = kw.get('payment_type')
        _response['merchant_order_id'] = kw.get('merchant_order_id')
        _response['preference_id'] = kw.get('preference_id')
        _response['site_id'] = kw.get('site_id')
        _response['processing_mode'] = kw.get('processing_mode')
        _response['merchant_account_id'] = kw.get('merchant_account_id')
        
        try:
            _response_html = self._mercadopago_reponse_formatter(_response)
            if(_response['collection_status']==str("pending") 
                or _response['collection_status']==str("success") 
                or _response['collection_status']==str("failure") 
                or _response['collection_status']==str("approved")
                or _response['collection_status']==str("rejected")
                or _response['collection_status']==str("in_process")):

                if('sale_order_id' in request.session):
                    current_sale_order_id = request.session.sale_order_id                                
                    sale_order = http.request.env['sale.order'].sudo().search([['id','=',current_sale_order_id]])
                    query = "select id from payment_acquirer where provider = 'mercadopago' limit 1"
                    request.cr.execute(query)
                    acquirer = request.cr.dictfetchone()
                    acquirer_id = False
                    if(acquirer['id']):
                        acquirer_id = acquirer['id']
                        if(_response['collection_status']==str("pending")
                            or _response['collection_status']==str("in_process")
                            or _response['collection_status']==str("failure") 
                            or _response['collection_status']==str("rejected")):

                            sale_order.sudo().write({'mp_response':_response_html}) 
                            sale_order.sudo().write({'mp_json_response':json.dumps(_response)})
                            sale_order.sudo().write({'reference':sale_order.name+str("-1")})
                            sale_order.sudo().write({'state':str("sent")})
                            if(request.session.uid!=None):
                                sale_order.sudo().write({'user_id':request.session.uid})                            
                            
                            sale_order.action_quotation_send()

                            if(_response['collection_status']==str("failure") 
                                or _response['collection_status']==str("rejected")):
                                return werkzeug.utils.redirect("/shop/payment?state=fail")
                            
                            return werkzeug.utils.redirect("/shop/confirmation?state=quoted")                             
                            #return http.request.render("website_sale.confirmation", {'order': sale_order})

                        elif(_response['collection_status']==str("success") 
                            or _response['collection_status']==str("approved")):
                            payment_transaction = request.env['payment.transaction'].sudo().create({'partner_id':sale_order.partner_id.id,'partner_name':sale_order.partner_id.name,'date':datetime.datetime.now(),'acquirer_id':int(acquirer_id),'type':'form','state':'done','amount':sale_order.amount_total,'reference':sale_order.name+str("/mp-website"),'currency_id':sale_order.partner_id.currency_id.id})
                            payment_transaction.sudo().write({'mp_response':_response_html})
                            payment_transaction.sudo().write({'mp_json_response':json.dumps(_response)})
                            
                            query = "insert into sale_order_transaction_rel (sale_order_id,transaction_id) values("+str(current_sale_order_id)+","+str(payment_transaction.id)+")"
                            request.cr.execute(query) 

                            if(_response['payment_type']=="credit_card" 
                                or _response['payment_type']=="debit_card" 
                                or _response['payment_type']=="prepaid_card" 
                                or _response['payment_type']=="digital_currency" 
                                or _response['payment_type']== "account_money"):
                                require_payment = "TRUE"
                            else:
                                require_payment = "FALSE"
                            
                            currentDateTime = datetime.datetime.now()
                            currentTime = currentDateTime.strftime("%Y-%m-%d %H:%M:")

                            sale_order.sudo().write({'commitment_date':str(currentTime)})
                            sale_order.sudo().write({'require_payment':require_payment})
                            sale_order.sudo().write({'mp_response':_response_html})
                            sale_order.sudo().write({'mp_json_response':json.dumps(_response)})
                            sale_order.sudo().write({'reference':sale_order.name+str("-1")})
                            sale_order.sudo().write({'state':str("done")})                       

                            if(request.session.uid!=None):
                                sale_order.sudo().write({'user_id':request.session.uid})

                            sale_order.action_quotation_send()
                            sale_order.action_done()
                                
                                # get journal payu
                            mercadopago_journal = http.request.env['account.journal'].sudo().search([['code','=','MEPGO']], order='id desc', limit=1)
                            move_name = "MEPGO/"+str(mercadopago_journal.sequence_number_next)
                            
                            # get last statement
                            last_account_bank_statement = http.request.env['account.bank.statement'].sudo().search([('company_id', '=', sale_order.company_id.id),('journal_id','=',mercadopago_journal.id)], order='id desc', limit=1)

                            # adds statement       
                            balance_end = float(last_account_bank_statement.balance_end) +  float(sale_order.amount_total)
                            difference = balance_end * -1
                            new_account_bank_statement = request.env['account.bank.statement'].sudo().create(
                                                                                                                {
                                                                                                                'name':str(sale_order.name)+str("-1"),
                                                                                                                'date':sale_order.date_order,
                                                                                                                'balance_start':last_account_bank_statement.balance_end,
                                                                                                                'balance_end_real':format(balance_end, '.2f'),
                                                                                                                'state':str('open'),
                                                                                                                'journal_id':int(mercadopago_journal.id),
                                                                                                                'company_id':int(sale_order.company_id.id),
                                                                                                                'total_entry_encoding':format(float(last_account_bank_statement.balance_end), '.2f'),
                                                                                                                'balance_end':format(balance_end, '.2f'),
                                                                                                                'difference':format(difference, '.2f'),
                                                                                                                'user_id':int(sale_order.user_id),
                                                                                                                'create_uid':int(sale_order.user_id),
                                                                                                                'create_date':str(sale_order.date_order),
                                                                                                                'write_uid':int(sale_order.user_id),
                                                                                                                'write_date':str(sale_order.date_order),
                                                                                                                }
                                                                                                            )
                            # adds statement line
                            new_account_bank_statement_line = request.env['account.bank.statement.line'].sudo().create (
                                                                                                                            {
                                                                                                                            'name':'mercadopago - '+str(sale_order.reference),
                                                                                                                            'move_name':move_name, 
                                                                                                                            'ref':sale_order.reference, 
                                                                                                                            'date':sale_order.date_order, 
                                                                                                                            'journal_id':int(mercadopago_journal.id),
                                                                                                                            'partner_id':int(sale_order.partner_id.id),
                                                                                                                            'company_id':int(sale_order.company_id.id),  
                                                                                                                            'create_uid':int(sale_order.user_id),
                                                                                                                            'create_date':str(sale_order.date_order),
                                                                                                                            'write_uid':int(sale_order.user_id),
                                                                                                                            'write_date':str(sale_order.date_order),
                                                                                                                            'statement_id':int(new_account_bank_statement.id),
                                                                                                                            'sequence':int(1),
                                                                                                                            'amount_currency':float(0.00),
                                                                                                                            'amount':format(float(sale_order['amount_total']), '.2f'),
                                                                                                                            }
                                                                                                                        )  
                            #with open('/odoo_diancol/custom/addons/mercadopago/log.json', 'w') as outfile:
                            #    json.dump(_response, outfile)
                            #return werkzeug.utils.redirect("/shop/confirmation") 
                            
                            return werkzeug.utils.redirect("/shop/confirmation?state=done")
            else:
                #with open('/odoo_diancol/custom/addons/mercadopago/log.json', 'w') as outfile:
                #    json.dump(_response, outfile)
                return werkzeug.utils.redirect("/shop/payment")

            #self.file_put_contents('/odoo_diancol/custom/addons/mercadopago/static/src/form/response.html',_response_html)
        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/odoo_13/custom/addons/mercado__pago/log.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            return werkzeug.utils.redirect("/shop/payment")
    
    def file_get_contents(self, filename):
        with open(filename) as f:
            return f.read()

    def file_put_contents(self, filename,data):
        with open(filename,'w') as f:
            return f.write(data)
    
    def _mercadopago_reponse_formatter(self, _response):

        _statusText = {
                        "null":"",
                        "pending":"Transacción pendiente o en validación",
                        "success":"Transacción aprobada",
                        "approved":"Transacción aprobada",
                        "failure":"Transacción expirada",
                        "rejected":"Transacción rechazada",
                        "in_process":"Transacción en proceso",
                      }
        _ml_sites = {
                        "MCO":["Colombia",['credit_card','ticket','bank_transfer','account_money']],
                        "MLA":["Argentina",['credit_card','debit_card','ticket','atm','account_money']],
                        "MLC":["Chile",['credit_card','ticket','bank_transfer','account_money']],
                        "MLB":["Brasil",['credit_card','ticket','digital_currency','account_money']],
                        "MLM":["México",['credit_card','debit_card','prepaid_card','ticket','atm','account_money','digital_currency']],
                        "MLU":["Uruguay",['credit_card','atm','account_money']],
                        "MPE":["Perú",['credit_card','debit_card','atm','account_money']],
                    }
        _ml_payment_types = {
                                'credit_card':'Tarjeta Crédito',
                                'debit_card':'Tarjeta Débito',
                                'ticket':'Ticket',
                                'bank_transfer':'Transferencia Bancaria',
                                'account_money':'Dinero en Cuenta',
                                'atm':'Cajeros Automáticos',
                                'digital_currency':'Divisa Digital',
                            }
        
        # collection_id
        # collection_status : null, pending (ticket,pse), success (cards,pse), failure (cards, pse)
        # external_reference
        # payment_type : ticket (baloto), cards (visa, mastercard), pse (bancos)
        # merchant_order_id
        # preference_id
        # site_id (MCO) it dependes with account credentials
        # processing_mode : frecuently aggregator
        # merchant_account_id : frecuently null

        site_name = _ml_sites[_response['site_id']][0]
        payment_type_name = _ml_payment_types[_response['payment_type']]
        status = _statusText[_response['collection_status']]

        _response_html = str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("Estado: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(status)
        _response_html = _response_html + str("</span>")
        _response_html = _response_html + str("</div>")

        

        _response_html = _response_html + str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("Localización: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(site_name)
        _response_html = _response_html + str("</span>")
        _response_html = _response_html + str("</div>")

        _response_html = _response_html + str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("Tipo Pago: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(payment_type_name)
        _response_html = _response_html + str("</span>")
        _response_html = _response_html + str("</div>")

        _response_html = _response_html + str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("ID Pedido: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(_response['merchant_order_id'])
        _response_html = _response_html + str("</span>")
        _response_html = _response_html + str("</div>")

        _response_html = _response_html + str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("ID Preferencia: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(_response['preference_id'])
        _response_html = _response_html + str("</span>")
        _response_html = _response_html + str("</div>")

        return _response_html