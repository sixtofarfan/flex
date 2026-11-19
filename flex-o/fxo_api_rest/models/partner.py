# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
import requests
from odoo.exceptions import UserError, ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"
    
    method_registro = fields.Char(string='Metodo de Registro',default="Odoo")
    commercial_name = fields.Char(string='Nombre comercial')
    id_loges = fields.Char(string='Id Loges')

    
    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self.update_gamma()
        return res
    
    @api.constrains('company_id','company_type','is_supplier','is_customer','name','vat','l10n_latam_identification_type_id','street','email')
    def constrains_gamma(self):
        if self.method_registro == 'Odoo':
            self.update_gamma()

    def update_gamma(self):
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            if self.id_loges and self.vat :
                headers = {'Content-type': 'application/json'}
                datos = self.get_datos()
                if self.company_type == 'company':
                    r = requests.put('http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/partners.companys/'+str(self.id_loges)+ '/', data = json.dumps(datos), headers=headers)
                else :
                    r = requests.put('http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/partners.companys/'+str(self.id_loges)+ '/', data = json.dumps(datos), headers=headers)
                try:
                    validate = r.json()
                    if validate['status_code'] != 200:
                        raise UserError(r.text)
                except Exception as err:
                    raise UserError(r.text)		
                

    def get_datos(self):
        datos = {}
        t = self
        if t.company_type == 'company':
            datos =   {
                    "company_belonging": t.company_id.id if t.company_id.id else 5,
                    "company_type": "company",
                    "is_supplier": t.is_supplier,
                    "is_customer": t.is_customer,
                    "name": t.name,
                    "l10n_latam_identification_type_id": t.l10n_latam_identification_type_id.code_sunat,
                    "vat": t.vat if  t.vat else "",
                    "street": t.street if t.street else "" ,
                    "zip": t.zip if t.zip else "" ,
                    "phone_mobile": t.phone if t.phone else "" ,
                    "email": t.email if t.email else "" ,
                    "website": t.website if t.website else "" ,
                    "country_id": t.country_id.code if t.country_id.code else "" ,
                    "state_id": t.state_id.code if t.state_id.code else "",
                    "province_id":t.province_id.code if t.province_id.code else "",
                    "district_id": t.district_id.code if t.district_id.code else "",
                    "razon_comercial": t.name if t.name else "",
                    "code_client": t.ref if t.ref else "",
                    "credit_limit": t.credit_limit if t.credit_limit else 0,
                    "credit_days":0 , #t.property_payment_term_id.code if t.property_payment_term_id.code else 0 ,
                    "id_odoo": t.id
                }
        else :
            datos =   {
                        "company_belonging": t.company_id.id if t.company_id.id else 5,
                        "vat": t.vat if  t.vat else "",
                        "l10n_latam_identification_type_id": t.l10n_latam_identification_type_id.code_sunat,
                        "street": t.street if t.street else "",
                        "zip":  t.zip if t.zip else "",
                        "phone": t.phone if t.phone else "",
                        "country_id": t.country_id.code if t.country_id.code else "" ,
                        "state_id": t.state_id.code if t.state_id.code else "",
                        "province_id":t.province_id.code if t.province_id.code else "",
                        "district_id": t.district_id.code if t.district_id.code else "",
                        "company_type": "person",
                        "name":  t.name,
                        "email": t.email if t.email else "" ,
                        "position": t.function if t.function else "" ,
                        "type_contact": "1",
                        "id_odoo": t.id

                    }
            if t.parent_id.id:
                datos.update({'reference_type_document_company':t.parent_id.l10n_latam_identification_type_id.code_sunat})
                datos.update({'reference_number_document_company':t.parent_id.vat})
        return  datos

    def registro_loges(self):
        t = self
        r = []
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            if self.id_loges == False:
                if t.method_registro == "Odoo" and t.vat:
                    headers = {'Content-type': 'application/json'}
                    datos = self.get_datos()
                    if t.company_type == 'company':
                        r = requests.post('http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/partners.companys/', data = json.dumps(datos), headers=headers)
                    else :
                        r = requests.post('http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/partners.companys/', data = json.dumps(datos), headers=headers)
                    try:
                        validate = r.json()
                        if validate['status_code'] != 201:
                            raise UserError(r.text)
                        t.id_loges = validate['data']['id_loges']
                    except Exception as err:
                        raise UserError(r.text)					
        return t
    
