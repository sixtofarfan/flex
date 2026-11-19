# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class SaleOrderBomWizard(models.Model):
    _name = "sale.order.bom.wizard"

    name     = fields.Date(string='From')
    date_to  = fields.Date(string='to')

    @api.onchange('name', 'date_to')
    def onchange_name(self):
        if self.name and self.date_to:
            if self.date_to <= self.name:
                raise UserError( _('Dates incorrectly'))

    def set_sale_order_bom(self):
        temp = self.name
        while(True):
            qty = self.env['sale.order.bom'].search([('name','=',temp)])
            if len(qty) == 0:
                data = {'name': temp}
                t = self.env['sale.order.bom'].create(data)
            if temp == self.date_to :
                break
            else :
                temp += timedelta(days=1)
