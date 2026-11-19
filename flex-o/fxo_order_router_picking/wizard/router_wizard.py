# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class StockPockingRouter(models.TransientModel):
    _name = "stock.picking.router.wizard"
    _description = ' Generate Rourter from to'
    
    name     = fields.Date(string='From')
    date_to  = fields.Date(string='to')

    def set_router_line(self):
        ids = self.env.context['active_ids']
        router_id = self.env['stock.picking.router'].browse(ids)
        for item in router_id:
            temp = self.name
            while(True):
                qty = self.env['stock.picking.router.line'].search([
                    ('name','=',temp)
                    ])
                if len(qty) == 0:
                    data = {'name': temp}
                    t = self.env['stock.picking.router.line'].create(data)
                if temp == self.date_to :
                    break
                else :
                    temp += timedelta(days=1)
