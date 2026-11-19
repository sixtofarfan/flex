# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import json
import requests

from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"
    
    method_registro = fields.Char(string='Metodo de Registro',default="Odoo")
    id_loges = fields.Char(string='Id Loges')

    def set_datos(self,rec):
        datos =   {
                "company_id" : rec.company_id.id,
                "amount" : round(rec.amount, 2),
                "amount_me" : round(rec.amount_me, 2),
                "amount_mn" : round(rec.amount_mn, 2),
                "bank_statement_id" :rec.bank_statement_id.id if rec.bank_statement_id.id else  "",
                "batch_payment_id" : rec.batch_payment_id.id if rec.batch_payment_id.id  else "",
                "cash_flow_id" : rec.cash_flow_id.id if rec.cash_flow_id.id  else "" ,
                "cash_nro_comp" : rec.cash_nro_comp if rec.cash_nro_comp else "",
                "catalog_payment_id" : rec.catalog_payment_id.id if rec.catalog_payment_id.id  else "",
                "communication" : rec.communication if  rec.communication else "" ,
                "currency_id" : rec.currency_id.name,
                "display_name" : rec.display_name,
                "has_invoices" : rec.has_invoices,
                "hide_payment_method" : rec.hide_payment_method,
                "is_personalized_change" : rec.is_personalized_change,
                "journal_id" : rec.journal_id.id if rec.journal_id.id  else "",
                "manual_batch_payment_id" : rec.manual_batch_payment_id.id if rec.manual_batch_payment_id.id  else "" ,
                "move_name" : rec.move_name if rec.move_name else "",
                "move_reconciled" : rec.move_reconciled,
                "name" : rec.name,
                "nro_comp" : rec.nro_comp if rec.nro_comp else  "",
                "partner_bank_account_id" : rec.partner_bank_account_id.id if rec.partner_bank_account_id.id else "",
                "partner_type" : rec.partner_type if rec.partner_type else "",
                "doc_type" : rec.partner_id.l10n_latam_identification_type_id.code_sunat,
                "partner_id" : rec.partner_id.vat,
                "payment_date" : str(rec.payment_date)+" 00:00:00",
                "payment_method_id" : rec.payment_method_id.id,
                "payment_reference" : rec.payment_reference if rec.payment_reference  else "",
                "payment_type" : rec.payment_type if rec.payment_type else "" ,
                "state" :rec.state,
                "is_advance" : rec.is_advance,
                "type_change" : round(rec.type_change, 4),  
                "type_doc_cash_id" : rec.type_doc_cash_id.id if rec.type_doc_cash_id.id else "",
                "type_document_id" : rec.type_document_id.id if rec.type_document_id.id  else "",
                "type_document" : rec.type_document_id.code if rec.type_document_id.id  else "",
                "writeoff_account_id" : rec.writeoff_account_id.id if rec.writeoff_account_id.id  else "",
                "writeoff_label" : rec.writeoff_label if rec.writeoff_label else "" ,
                "type_service" : rec.order_id.type_id.code if rec.order_id.type_id.code else "" ,
                "number_operation" : rec.order_id.name if rec.order_id.name else "",
                "notes" : " ",
                "ref" : " ",
                "id_odoo" : rec.id
            }
        return datos

    @api.constrains("state")
    def update_loges(self):
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True" and self.id_loges and self.payment_type != "transfer":
            headers = {'Content-type': 'application/json'}
            datos = self.set_datos(self)
            json_data = json.dumps(datos)
            url = str(url_api) + 'api/1.0/synchronization/from.odoo/paymentandcollection/'+str(self.id_loges) +'/'
            r = requests.put(url, data =json_data , headers=headers)

            try:
                validate = r.json()
                if validate['status_code'] != 200:
                    raise UserError(r.text)
                else :
                    self.id_loges = validate['data']['id_loges'] 
            except Exception as err:
                raise UserError(r.text)

    def post(self):
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')

        super(AccountPayment,self).post()
        if status_api == "True":
            for rec in self:
                if rec.method_registro == "Odoo" and rec.payment_type != "transfer":
                    if rec.id_loges :
                        rec.update_loges()
                    else:
                        headers = {'Content-type': 'application/json'}
                        datos = rec.set_datos(rec)
                        json_data = json.dumps(datos)
                        r = requests.post(str(url_api) + 'api/1.0/synchronization/from.odoo/paymentandcollection/', data =json_data , headers=headers)
                        try:
                            validate = r.json()
                            if validate['status_code'] != 201:
                                raise UserError(r.text)
                            else:
                                rec.id_loges = validate['data']['id_loges'] 
                        except Exception as err:
                            raise UserError(r.text)	

    def unlink(self):
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            headers = {'Content-type': 'application/json'}
            if self.id_loges:
                url = str(url_api) + 'api/1.0/synchronization/from.odoo/paymentandcollection/' + str(self.id_loges) +"/" 
                r = requests.delete(url , headers=headers)
                print(r.text)
                validate = r.json()
                if validate['status_code'] != 200:
                    raise UserError(r.text)
        return super(AccountPayment, self).unlink()