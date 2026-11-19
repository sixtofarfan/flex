# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import json
import requests

from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.constrains("date_verify")
    def api_date_verify(self):
        url_api = self.env['ir.config_parameter'].sudo().get_param('url_api')
        status_api = self.env['ir.config_parameter'].sudo().get_param('state_api_gamma')
        if status_api == "True":
            if self.date_verify:
                headers = {'Content-type': 'application/json'}
                datos =   {
                            "type_document_client" : self.partner_id.l10n_latam_identification_type_id.code_sunat,
                            "number_document_client" : self.partner_id.vat,
                            "number_operation" :self.name,
                            "date_verify":str(self.date_verify),
                        }
                r = requests.put(str(url_api) + 'api/1.0/synchronization/from.odoo/saleorders/'+ str(self.id_loges) + '/', data =json.dumps(datos) , headers=headers)
                try:
                    validate = r.json()
                    if validate['status_code'] != 200:
                        raise UserError(r.text )
                except Exception as err:
                    raise UserError(r.text )