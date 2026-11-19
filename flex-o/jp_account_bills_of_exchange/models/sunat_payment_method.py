from odoo import models, fields, api, _

class SunatPaymentMethod(models.Model):
    _name = 'sunat.payment.method'
    _description = 'Sunat Payment Methods from Table1'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')