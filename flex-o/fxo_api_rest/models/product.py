
# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
import requests
from odoo.exceptions import UserError, ValidationError


class ProductoTemplate(models.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    
    method_registro = fields.Char(string='Metodo de Registro',default="None")
    id_loges = fields.Char(string='Id Loges')

    @api.model
    def create(self,vals):
        t = super(ProductoTemplate,self).create(vals)
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            if t.method_registro == "None":
                headers = {'Content-type': 'application/json'}
                datos =   {
                        "company_belonging": t.company_id.id if t.company_id.id else 5 ,
                        "name": t.name,
                        "type": t.type,
                        "is_sale": t.sale_ok,
                        "is_purchase": t.purchase_ok,
                        "code_odoo": t.default_code if t.default_code else "" ,
                        "cuenta_contable_gastos": t.property_account_expense_id.code if t.property_account_expense_id.code else "",
                        "cuenta_contable_ingresos": t.property_account_income_id.code if t.property_account_income_id.code else "",
                        "description" : t.description_sale if t.description_sale else t.name,
                        "id_odoo": t.id
                    }
                r = requests.post('http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/products/', data =json.dumps(datos) , headers=headers)
                print(r.text)
                try:
                    validate = r.json()
                    if validate['status_code'] != 201:
                        raise UserError(r.text)
                    t.method_registro = "Odoo"
                except Exception as err:
                    raise UserError(r.text)	
                
                t.id_loges = validate['data']['id_loges']
        return t
    
    def unlink(self):
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            headers = {'Content-type': 'application/json'}
            company_belonging = self.company_id.id if self.company_id.id else 5 
            if self.id_loges:
                url = 'http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/products/'+str(self.id_loges) +"/" 
                r = requests.delete(url , headers=headers)
                print(r.text)
                validate = r.json()
                if validate['status_code'] != 200:
                    raise UserError(r.text)
        return super(ProductoTemplate, self).unlink()

    @api.constrains('company_id','name','type','sale_ok','purchase_ok','default_code','property_account_expense_id','property_account_income_id','description')
    def update_gamma(self):
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            if self.id > 0 : 
                if self.method_registro == "Odoo" and self.id_loges:
                    headers = {'Content-type': 'application/json'}
                    datos =   {
                            "company_belonging": self.company_id.id if self.company_id.id else 5 ,
                            "name": self.name,
                            "type": self.type,
                            "is_sale": self.sale_ok,
                            "is_purchase": self.purchase_ok,
                            "code_odoo": self.default_code if self.default_code else "" ,
                            "cuenta_contable_gastos": self.property_account_expense_id.code if self.property_account_expense_id.code else "",
                            "cuenta_contable_ingresos": self.property_account_income_id.code if self.property_account_income_id.code else "",
                            "description" : self.description_sale if self.description_sale else self.name,
                            "id_odoo": self.id
                        }
                    company_belonging = self.company_id.id if self.company_id.id else 5 
                    url = 'http://191.98.144.12:5000/api/1.0/synchronization/from.odoo/products/'+str(self.id_loges) +"/" 

                    r = requests.put(url, data =json.dumps(datos) , headers=headers)
                    print(r.text)
                    validate = r.json()
                    if validate['status_code'] != 200:
                        raise UserError(r.text)
