# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning


class PurcahseOrder(models.Model):

    _inherit = "purchase.order"

    import_number = fields.Char(string='Import N°')

    def action_view_invoice(self):
        res = super (PurcahseOrder, self).action_view_invoice()
        context = res['context']
        type_document_id = self.env['einvoice.catalog.01'].search([('code','=','01')], limit=1)
        context['default_type_document_id'] = type_document_id.id
        context['default_import_number'] = self.import_number 
        res['context'] = context
        return res
    
    # def name_get(self):
    #     result = []
    #     for order in self:
    #         result.append([order.id,order.import_number + ' [' + order.name + ']'])
    #     return result