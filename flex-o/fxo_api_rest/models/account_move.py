# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import json
import requests

from odoo.exceptions import UserError, ValidationError

class AccountMove(models.Model):
    _inherit = "account.move"
    
    method_registro = fields.Char(string='Metodo de Registro',default="Odoo")
    id_loges = fields.Char(string='Id Loges')
    api_aplicaciones = fields.Char(string='api_aplicaciones')
    bill_to_typedocument = fields.Many2one(comodel_name='l10n_latam.identification.type', string='Tipo de Documento a Cobrar')
    bill_to_numberdocument = fields.Many2one(comodel_name='res.partner', string='Partner a Cobrar ')
    
    @api.constrains("state")
    def update_loges_state(self):
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        if status_api == "True" and  self.id_loges:
            if self.method_registro == "Odoo" and self.type in ["in_invoice","in_refund","in_receipt"]:
                headers = {'Content-type': 'application/json'}
                datos =     {
                                "status_invoice_supplier" : self.state
                            }
                r = requests.put(str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoice/update_status/'+ str(self.id_loges)+'/', data =json.dumps(datos) , headers=headers)
                validate = r.json()
                if validate['status_code'] != 200:
                    raise UserError(r.text )


    @api.constrains("amount_residual")
    def update_api_aplicacioness(self):
        for item in self:
            if item.amount_total != item.amount_residual:
                item.get_api_aplicaciones()

    def action_post(self):
        super(AccountMove,self).action_post()
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        value_unaffected = 0
        for item in self.invoice_line_ids:
            for tax in item.tax_ids:
                if tax.l10n_pe_edi_tax_code == "9998":
                    value_unaffected += round(item.price_subtotal, 2)

        if status_api == "True":
            if self.method_registro == "Odoo" and self.type in ["in_invoice","in_refund","in_receipt"]:
                headers = {'Content-type': 'application/json'}
                datos =   {
                            "company_belonging" : self.company_id.id ,# Id Empresa,
                            "type_document_provider" : self.partner_id.l10n_latam_identification_type_id.code_sunat,
                            "number_document_provider" : self.partner_id.vat,
                            "date_emission" : str(self.invoice_date)+ " 00:00:00" ,
                            "expenses_document_series" : self.ref[0:4],
                            "number_document_expenses" : self.ref[5:],
                            "type_coin_expenses" : self.currency_id.name,
                            "rate_exchange" : round(self.currency_rate, 3),
                            "tax_base" : round(self.amount_untaxed, 2) - value_unaffected,
                            "value_igv" : round(self.amount_tax, 2),
                            "value_unaffected" : round(value_unaffected, 2),
                            "total_amount" : round(self.amount_total, 2),
                            "code_client" : self.partner_id.ref if self.partner_id.ref else "" ,
                            "type_origin" : self.journal_id.code,
                            "number_voucher" : self.name,
                            "month_voucher" : self.invoice_date.day,
                            "date_creation" : str(self.create_date),
                            "date_modification" : str(self.create_date),
                            "type_invoice" : self.type_invoice if self.type_invoice else "",
                            "type_document_expenses": self.type_document_id.code,
                            "number_operation_odoo" :  self.name,
                            "status_invoice_supplier": self.state,
                            "id_odoo":self.id
                        }
                print(datos)
                r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoice/', data =json.dumps(datos) , headers=headers)
                try:
                    validate = r.json()
                    if validate['status_code'] != 201:
                        raise UserError(r.text )
                except Exception as err:
                    raise UserError(r.text )
                if validate['status_code'] == 201:
                    print(validate)
                    self.id_loges = validate['data']['id_loges']
                    for item in self.invoice_line_ids:
                        line  = {
                                "company_belonging": item.company_id.id ,
                                "type_document_provider": self.partner_id.l10n_latam_identification_type_id.code_sunat,
                                "number_document_provider": self.partner_id.vat,
                                "expenses_document_series": item.ref[0:4],
                                "number_document_expenses": item.ref[5:],
                                "type_document_expenses": self.type_document_id.code,
                                "code_concept": item.product_id.default_code,
                                "name_concept": item.product_id.name,
                                "import_item_expenses": round(item.price_subtotal, 2),
                                "type_service": item.order_id.type_id.code  if item.order_id.id else '' ,
                                "number_operation": item.order_id.name if item.order_id.id else '',
                                "reference_document_payment": item.name,
                                "unit_price": round(item.price_unit, 2),
                                "quantity": item.quantity,
                                "analytic_account": item.analytic_account_id.code if item.analytic_account_id.id else "",
                                "code_odoo":item.id,
                                "subtotal" :  round(item.price_subtotal, 2),
                                "total": round(item.price_total, 2),
                                "id_odoo":item.id
                            }
                        r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoicedetails/', data =json.dumps(line) , headers=headers)
                        print(line)
                        try:
                            validate = r.json()
                            if validate['status_code'] != 201:
                                self.id_loges = validate['data']['id_loges'] 
                                raise UserError(r.text)
                        except Exception as err:
                            raise UserError(r.text)		
                else :
                    raise UserError(r.text)

    def button_annul(self):
        res = super().button_annul()
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        if status_api == "True":
            if self.id_loges  and self.type == "in_invoice":
                headers = {'Content-type': 'application/json'}
                datos =   {
                            "company_belonging" : self.company_id.id ,# Id Empresa,
                            "type_document_provider" : self.partner_id.l10n_latam_identification_type_id.code_sunat,
                            "number_document_provider" : self.partner_id.vat,
                            "date_emission" : str(self.invoice_date)+ " 00:00:00" ,
                            "expenses_document_series" : self.ref[0:4],
                            "number_document_expenses" : self.ref[5:],
                            "type_coin_expenses" : self.currency_id.name,
                            "rate_exchange" :  round(self.currency_rate, 3),
                            "tax_base" : round(self.amount_untaxed, 2),
                            "value_igv" : round(self.amount_tax, 2),
                            "value_unaffected" : round(self.amount_untaxed, 2),
                            "total_amount" : round(self.amount_total, 2),
                            "code_client" : self.partner_id.ref if self.partner_id.ref else "" ,
                            "type_origin" : self.journal_id.code,
                            "number_voucher" : self.name,
                            "month_voucher" : self.invoice_date.day,
                            "date_creation" : str(self.create_date),
                            "date_modification" : str(self.create_date),
                            "type_invoice" : self.type_invoice if self.type_invoice else "",
                            "type_document_expenses": self.type_document_id.code,
                            "number_operation_odoo" :  self.name,
                            "status_invoice_supplier": "annul",
                            "id_odoo":self.id
                        }
                r = requests.put(str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoice/'+str(self.id_loges) + "/", data =json.dumps(datos) , headers=headers)
                print("anull " +str(self.id_loges) )
                try:
                    validate = r.json()
                    if validate['status_code'] != 200:
                        raise UserError(r.text )
                except Exception as err:
                    raise UserError(r.text )

        return res

    def get_api_aplicaciones(self):
        for rec in self:
            rec.api_aplicaciones = " "
            if rec.invoice_payments_widget:
                dates = []
                parse_dict = json.loads(rec.invoice_payments_widget)
                if parse_dict:
                    self.enviar_cabezera(rec)
                    for pay in parse_dict.get('content'):
                        self.enviar_id_api_datos(pay,rec)
                    rec.api_aplicaciones = rec.invoice_payments_widget
                else:
                    rec.api_aplicaciones = rec.invoice_payments_widget	
            else:
                rec.api_aplicaciones = " "
      
    def enviar_cabezera(self,rec):
        t = rec
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        if status_api == "True" and t.type == "out_invoice" and t.partner_id and t.ref:
            headers = {'Content-type': 'application/json'}
            original_amount = t.amount_total

            datos = {
                        "company_belonging": t.company_id.id,
                        "number_identy_application": t.ref if t.ref else "",
                        "type_document_partner": t.partner_id.l10n_latam_identification_type_id.code_sunat  if t.partner_id.l10n_latam_identification_type_id.code_sunat else "",
                        "number_document_partner": t.partner_id.vat  if t.partner_id.vat else "",
                        "type_document_invoicing": t.type_document_id.code  if t.type_document_id.code else "",
                        "serie_document_invoicing": t.ref[0:4] if t.ref else "",
                        "number_document_invoicing": t.ref[5:] if t.ref else "",
                        "date_emission": str(t.create_date),
                        "type_partner": "C",
                        "type_coin": t.currency_id.name  if t.currency_id.name else "PEN" 	,
                        "charge": round(t.amount_total, 2),
                        "deposit": round(0, 2),
                        "id_odoo_voucher": "",
                        "voucher": "",
                        "type_payment_table": "",
                        "rate_exchange": round(t.currency_rate, 3),
                        "original_amount": round(original_amount, 2) ,
                        "type_operation": t.invoice_line_ids[0].type_id.code  if t.invoice_line_ids[0].type_id.code  else "",
                        "number_operation": t.invoice_line_ids[0].order_id.name  if  t.invoice_line_ids[0].order_id.name  else "",
                        "id_odoo": t.id,
                        "status_conciliate": "C"
                    }
            r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/application_detail/', data =json.dumps(datos) , headers=headers)
            try:
                validate = r.json()
                if validate['status_code'] != 201:
                    raise UserError(r.text)
            except Exception as err:
                raise UserError(r.text)

    def enviar_id_api_datos(self,pay,rec):
        t = rec
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        payment = self.env['account.payment'].sudo().search([('id', '=', int(pay['account_payment_id']) ) ])
        move_id = self.env['account.move'].sudo().search([('id', '=', int(pay['move_id'])  )]) 
        bill_form_id = ""
        
        for item in move_id.line_ids:
            if not any(line.account_id == item.account_id for line in self.line_ids):

                reconciled_moves = item.mapped('matched_debit_ids.debit_move_id.move_id')\
                                + item.mapped('matched_credit_ids.credit_move_id.move_id')
                if len(reconciled_moves):
                    payment = reconciled_moves.line_ids[0].payment_id
        
        if  len(payment)==0:  
            for item in move_id.line_ids:
                if not any(line.account_id == item.account_id for line in self.line_ids):
                    reconciled_moves = item.mapped('matched_debit_ids.debit_move_id.move_id')\
                                    + item.mapped('matched_credit_ids.credit_move_id.move_id')
                    if len(payment) ==0:
                        if len(bill_form_id) ==0:
                            for line in reconciled_moves.line_ids:
                                bill_form_id = line.bill_form_id

        currency_rate = move_id.currency_rate
        voucher = ""
        type_payment_table = ""
        id_odoo_voucher = ""
        if len(payment) > 0:
            id_odoo_voucher = payment.id
            if payment.catalog_payment_id.id :
                voucher += payment.catalog_payment_id.description
                voucher += " "
            voucher += payment.name
            type_payment_table = "PAC"
            original_amount = pay['amount']

            if pay['currency'] == "$" and payment.currency_id.name == "USD":
                original_amount = pay['amount']
            elif pay['currency'] == "S/" and payment.currency_id.name == "PEN":
                 original_amount = pay['amount']
            elif pay['currency'] == "$" and payment.currency_id.name == "PEN":
                original_amount = pay['amount'] * currency_rate
            elif pay['currency'] == "S/" and payment.currency_id.name == "USD":
                original_amount = pay['amount'] / currency_rate
        elif len(bill_form_id) > 0 :
            id_odoo_voucher = bill_form_id.id
            voucher += bill_form_id.name
            type_payment_table = "CC"
        elif self.bill_form_id.id:
            id_odoo_voucher = self.bill_form_id.id
            voucher += self.bill_form_id.name
            payment =  self.bill_form_id
            type_payment_table = "CC"
        elif len(move_id) > 0:
            voucher = move_id.ref if  move_id.ref  else move_id.name
            id_odoo_voucher = move_id.id
            type_payment_table = "I"
        if status_api == "True" and t.type == "out_invoice" and t.partner_id and t.ref:
            headers = {'Content-type': 'application/json'}
            original_amount = t.amount_total

            datos = {
                        "company_belonging": t.company_id.id,
                        "number_identy_application": t.ref if t.ref else "",
                        "type_document_partner": t.partner_id.l10n_latam_identification_type_id.code_sunat  if t.partner_id.l10n_latam_identification_type_id.code_sunat else "",
                        "number_document_partner": t.partner_id.vat  if t.partner_id.vat else "",
                        "type_document_invoicing": t.type_document_id.code  if t.type_document_id.code else "",
                        "serie_document_invoicing": t.ref[0:4] if t.ref else "",
                        "number_document_invoicing": t.ref[5:] if t.ref else "",
                        "date_emission": str(t.create_date),
                        "type_partner": "C",
                        "type_coin": "USD"  if pay['currency'] == "$" else "PEN" 	,
                        "charge": round(0, 2),
                        "deposit": round(pay['amount'], 2),
                        "id_odoo_voucher": id_odoo_voucher,
                        "voucher": voucher  if voucher else move_id.name,
                        "type_payment_table": type_payment_table,
                        "rate_exchange": round(currency_rate, 3),
                        "original_amount": round(original_amount, 2) ,
                        "type_operation": t.invoice_line_ids[0].type_id.code  if t.invoice_line_ids[0].type_id.code  else "",
                        "number_operation": t.invoice_line_ids[0].order_id.name  if  t.invoice_line_ids[0].order_id.name  else "",
                        "id_odoo": str(self.id) +"-"+ str(pay['move_id']),
                        "status_conciliate": "C"
                    }
            rest = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/application_detail/', data =json.dumps(datos) , headers=headers)
            try:
                validate = rest.json()
                if validate['status_code'] == 201 :
                    pass
                else :
                    print(rest.text)
                    raise UserError(rest.text)
            except Exception as err:
                print(rest.text)
                raise UserError(rest.text)

    def unlink(self):
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            headers = {'Content-type': 'application/json'}
            for inv in self:
                if inv.id_loges:
                    url = str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoice/' + str(inv.id_loges) +"/" 
                    r = requests.delete(url , headers=headers)
                    for item in self.invoice_line_ids:
                        url = str(url_api) + 'api/1.0/synchronization/from.odoo/supplierinvoicedetails/' + str(item.id_loges) +"/" 
                        r = requests.delete(url , headers=headers)
        return super(AccountMove, self).unlink()

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    id_loges = fields.Char(string='Id Loges')
    bill_to_numberdocument = fields.Many2one(comodel_name='res.partner', string='Partner a Cobrar ')
    
    def remove_move_reconcile(self):
        document_id = self.env.context 
        for line in self:
            move_id = line.move_id 
            url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
            status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
            t = move_id
            if document_id.get('move_id'):
                id_odoo = str(document_id['move_id']) +"-"+ str(t.id)
                id_odoo2 = str(t.id)  +"-"+ str(document_id['move_id'])
                if status_api == "True" and  move_id.id:
                    headers = {'Content-type': 'application/json'}
                    original_amount = 0

                    datos = {
                                "company_belonging": t.company_id.id,
                                "number_identy_application": t.ref if t.ref else "",
                                "type_document_partner": t.partner_id.l10n_latam_identification_type_id.code_sunat  if t.partner_id.l10n_latam_identification_type_id.code_sunat else "",
                                "number_document_partner": t.partner_id.vat  if t.partner_id.vat else "",
                                "type_document_invoicing":  "",
                                "serie_document_invoicing": "",
                                "number_document_invoicing":  "",
                                "date_emission": str(t.create_date),
                                "type_partner": "C",
                                "type_coin": t.currency_id.name  if t.currency_id.name else "PEN" 	,
                                "charge": round(0, 2),
                                "deposit": round(0, 2),
                                "id_odoo_voucher": "",
                                "voucher": "",
                                "type_payment_table": "",
                                "rate_exchange": round(0, 3),
                                "original_amount": 0,
                                "type_operation": t.invoice_line_ids[0].type_id.code  if t.invoice_line_ids[0].type_id.code  else "",
                                "number_operation": t.invoice_line_ids[0].order_id.name  if  t.invoice_line_ids[0].order_id.name  else "",
                                "id_odoo": id_odoo ,
                                "status_conciliate": "N"
                            }
                    url = str(url_api) + 'api/1.0/synchronization/from.odoo/application_detail/by_odoo/' + str(id_odoo) +"/"
                    r = requests.put(url, data =json.dumps(datos) , headers=headers)
                    
                    datos = {
                                "company_belonging": t.company_id.id,
                                "number_identy_application": t.ref if t.ref else "",
                                "type_document_partner": t.partner_id.l10n_latam_identification_type_id.code_sunat  if t.partner_id.l10n_latam_identification_type_id.code_sunat else "",
                                "number_document_partner": t.partner_id.vat  if t.partner_id.vat else "",
                                "type_document_invoicing":  "",
                                "serie_document_invoicing": "",
                                "number_document_invoicing":  "",
                                "date_emission": str(t.create_date),
                                "type_partner": "C",
                                "type_coin": t.currency_id.name  if t.currency_id.name else "PEN" 	,
                                "charge": round(0, 2),
                                "deposit": round(0, 2),
                                "id_odoo_voucher": "",
                                "voucher": "",
                                "type_payment_table": "",
                                "rate_exchange": round(0, 3),
                                "original_amount": 0,
                                "type_operation": t.invoice_line_ids[0].type_id.code  if t.invoice_line_ids[0].type_id.code  else "",
                                "number_operation": t.invoice_line_ids[0].order_id.name  if  t.invoice_line_ids[0].order_id.name  else "",
                                "id_odoo": id_odoo2 ,
                                "status_conciliate": "N"
                            }
                    url = str(url_api) + 'api/1.0/synchronization/from.odoo/application_detail/by_odoo/' + str(id_odoo2) +"/"
                    r = requests.put(url, data =json.dumps(datos) , headers=headers)
        res = super(AccountMoveLine, self).remove_move_reconcile()
        return res

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    id_loges = fields.Char(string='Id Loges')

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    id_loges = fields.Char(string='Id Loges')

class AccountTax(models.Model):
    _inherit = "account.tax"
    
    code_loges = fields.Char(string='Codigo Loges')