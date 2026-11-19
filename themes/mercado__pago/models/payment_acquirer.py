# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import mercadopago
import json
import sys
import datetime
from odoo.http import request

class payment_acquirer_mercadopago(models.Model):
    _inherit = 'payment.acquirer'    

    provider = fields.Selection(selection_add=[('mercadopago', 'mercadopago')])
    mp_service_mode = fields.Selection([("basic","Básico"),("custom","Personalizado")], string='Modo Checkout', required_if_provider='mercadopago')
    # basic
    mp_client_id = fields.Char(string='ID Cliente')
    mp_client_secret = fields.Char(string='Clave Secreta')

    # custom
    mp_public_key = fields.Char(string='Clave Publica')    
    mp_access_token = fields.Char(string='Token de Acceso')   

    # countries
    mp_country =  fields.Selection([("MCO","Colombia"),("MPE","Perú"),("MLA","Argentina"),("MLC","Chile"),("MLB","Brasil"),("MLM","México"),("MLV","Venezuela")], string='País', required_if_provider='mercadopago')

    
    def mercadopago_sync_orders_payments(self):
        try:            
            acquirer = request.env['payment.acquirer'].sudo().search([['provider','=','mercadopago']], order='id asc', limit=1)
            mp = mercadopago.MP(acquirer.mp_access_token)   
            # '&',['state','!=','done'],         
            pending_sale_orders = request.env['sale.order'].sudo().search([['mp_json_response','!=','']], order='id asc')
            
            for sale_order in pending_sale_orders:
                
                mp_json_response = json.loads(str(sale_order.mp_json_response))
                collection_id = mp_json_response['collection_id']
                
                payment_info = mp.get_payment_info(str(collection_id))
                if(payment_info['status']==200 or payment_info['status']==201):
                    current_status_detail = None
                    if('status_detail' in mp_json_response):
                        current_status_detail = mp_json_response['status_detail']

                    payment_info = payment_info ['response']
                    mp_json_response['collection_status'] = payment_info['status']
                    mp_json_response['status_detail'] = payment_info['status_detail']
                    mp_json_response['status'] = payment_info['status']
                    mp_json_response['card'] = payment_info['card']                    
                    
                    if ('payment_method_id' in payment_info):
                        if(payment_info['payment_method_id']=="pse"):  
                            if('transaction_details' in payment_info):
                                if('external_resource_url' in payment_info['transaction_details']):
                                    mp_json_response['external_resource_url'] = payment_info['transaction_details']['external_resource_url']                                                       

                    _response_html = self._mercadopago_reponse_formatter(mp_json_response)
                    sale_order.sudo().write({'mp_json_response':json.dumps(mp_json_response)})  
                    sale_order.sudo().write({'mp_response':_response_html})

                    if(payment_info['status_detail']=="accredited"):
                        if(current_status_detail):
                            if(str(payment_info['status_detail'])!=(current_status_detail)):

                                query = "select sale_order_id, transaction_id from sale_order_transaction_rel where sale_order_id = "+str(sale_order.id) + " order by transaction_id desc limit 1"
                                request.cr.execute(query) 
                                sale_order_transaction_rel = request.cr.dictfetchone()
                                #with open('/odoo_diancol/custom/addons/mercadopago/log.json', 'w') as outfile:
                                #        json.dump((sale_order_transaction_rel['transaction_id']), outfile)
                                payment_transaction = request.env['payment.transaction'].sudo().search([['id','=',sale_order_transaction_rel['transaction_id']]], order='id desc', limit=1)
                                
                                payment_transaction.sudo().write({'mp_response':_response_html})
                                payment_transaction.sudo().write({'state':"done"})

                                #if('card' in mp_json_response and (mp_json_response['payment_type']=="credit_card" or mp_json_response['payment_type'] == "debit_card")):
                                #    with open('/odoo_diancol/custom/addons/mercadopago/log.json', 'w') as outfile:
                                #        json.dump((sale_order_transaction_rel['transaction_id']), outfile)

                                # get journal payu
                                mercadopago_journal = request.env['account.journal'].sudo().search([['code','=','MEPGO']], order='id desc', limit=1)
                                move_name = "MEPGO/"+str(mercadopago_journal.sequence_number_next)
                                
                                # get last statement
                                last_account_bank_statement = request.env['account.bank.statement'].sudo().search([('company_id', '=', sale_order.company_id.id),('journal_id','=',mercadopago_journal.id)], order='id desc', limit=1)

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
                                sale_order.action_done()
                    
                    #self.env['mail.message'].create({'message_type':"notification",
                    #    "subtype": self.env.ref("mail.mt_comment").id, # subject type
                    #    'body': "Message body",
                    #    'subject': "Message subject",
                    #    'needaction_partner_ids': [(4, self.user_id.partner_id.id)],   # partner to whom you send notification
                    #    'model': self._name,
                    #    'res_id': self.id,
                    #    })
                   
        except Exception as e:
            exc_traceback = sys.exc_info()
            #with open('/odoo_diancol/custom/addons/mercadopago/log.json', 'w') as outfile:
            #    json.dump(getattr(e, 'message', repr(e))+" ON LINE "+format(sys.exc_info()[-1].tb_lineno), outfile)
            

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
        status_detail = str("")
        if('status_detail' in _response):
            status_detail = str(" - ") + str(_response['status_detail'])                

        _response_html = str("<div>")
        _response_html = _response_html + str("<label>")
        _response_html = _response_html + str("Estado: ")
        _response_html = _response_html + str("</label>")
        _response_html = _response_html + str("<span>")
        _response_html = _response_html + str(status) + str(status_detail)
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

        if ('external_resource_url' in  _response):
            payment_type_name = str("<a href='"+_response['external_resource_url']+"' target='_blank'>") + str(payment_type_name)+str("</a>")

        _response_html = _response_html + str(payment_type_name)
        _response_html = _response_html + str("</span>")

        card = str("")
        if('card' in _response and (_response['payment_type']=="credit_card" or _response['payment_type'] == "debit_card")):
            if('first_six_digits' in _response['card']):
                card = str("*****") + str(_response['card']['first_six_digits']) + str(" expira el ") + str(_response['card']['expiration_month']) + str(" - ") + str(_response['card']['expiration_year'])
                _response_html = _response_html + str("<span><br/>")
                _response_html = _response_html + str("       ") + str(card)
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