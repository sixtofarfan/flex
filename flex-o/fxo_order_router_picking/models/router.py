# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class StockPickingRouter(models.Model):
    _name = "stock.picking.router"
    _description = 'Router'

    name = fields.Char(string='Name')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')],
                             string='State',
                             default='draft')
    # router_lien_id = fields.One2many(comodel_name='stock.picking.router.line',
    #                                  inverse_name='router_id',
    #                                  string='Router')
    # driver_id = fields.One2many(comodel_name='stock.picking.router.drive',
    #                             inverse_name='name',
    #                             string='Drivers')


# class StockPickingDrive(models.Model):
#     _name = "stock.picking.router.drive"
#     _description = 'Drive router'

#     sequence = fields.Integer(default=10)
#     name = fields.Many2one(comodel_name='stock.picking.router', string='Router')
#     driver_id = fields.Many2one(comodel_name='res.partner', string='Driver')
#     qty = fields.Integer(string='Qty',default=0)

#     @api.constrains('qty', 'driver_id')
#     def onchange_qty(self):
#         cant = 0
#         if self.driver_id.id :
#             qty = self.env['stock.picking.router.drive'].search([
#                 ('driver_id', '=', self.driver_id.id)
#             ])
#             for item in qty:
#                 cant += item.qty
#             if cant > self.driver_id.capacity:
#                 raise UserError(str(self.driver_id.name) + ' only has a capacity of '+ str(self.driver_id.capacity) + ' and is being assigned ' + str(cant))



class StockPickingRouterLine(models.Model):
    _name = "stock.picking.router.line"
    _order = 'name desc'
    _description = ' Router Day'

    name  = fields.Date(string='Day')

    drivers_id = fields.Many2many(comodel_name='res.partner', string='Drivers')


    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
    ],string='State',default='draft')

    orders_id = fields.Many2many(
        comodel_name='sale.order',
        string='Orders',
        compute='_compute_orders_id',
    )


    # @api.constrains('state')
    # def constrains_state(self):
    #     for order in self.orders_id:
    #         if order.router_partner.id == False:
    #             raise UserError('assigned Drive at Order ' + str(order.name))

    @api.model
    def _compute_orders_id(self):
        for item in self:
            item.orders_id  = item.get_ordes()

    def get_ordes(self):
        date = datetime.strptime(str(self.name) + " 00:00:00",'%Y-%m-%d %H:%M:%S')
        order = self.env['sale.order'].sudo().search([
            ('state', '=', 'done'),
            ('router', '!=', False),
            ('commitment_date', '>=', date),
            ('commitment_date', '<=', date +
             timedelta(hours=23, minutes=59, seconds=59, microseconds=999999))
        ])

        return order

    def set_drive(self,orders_id):
        date = datetime.strptime(str(self.name) + " 00:00:00",'%Y-%m-%d %H:%M:%S')
        drives_id = self.env["stock.picking.router.drive"].search([])
        for drive in drives_id:
            con = 1
            orders = self.env['sale.order'].sudo().search([
                ('state', '=', 'done'), ('router', '!=', False),
                ('commitment_date', '>=', date),
                ('router', 'in', drive.driver_id.ids),
                ('commitment_date', '<=', date + timedelta(
                    hours=23, minutes=59, seconds=59, microseconds=999999))
            ])
            if len(orders) > 0:
                self.drivers_id += drive.name

            for order in orders:
                if drive.qty >= con:
                    order.router_partner = drive.name.id
                    order.router_day = self.id
                    con += 1
                else:
                    break

    def get_drive(self,index):
        temp = self.env["stock.picking.router.drive"].search([
            ('id','>',index)
        ], limit=1)

        return temp

    def set_state_router_draft(self):
        state = 'draft'
        for item in self.orders_id :
            item.state_router = state
            item.router_partner = False
        self.state = state

    def set_state_confirm(self):
        state = 'confirm'
        self.set_drive(self.orders_id)

        for item in self.orders_id:
            item.state_router = state
        self.state = state

    _sql_constraints = [
        ('name_uniq', 'unique (name)',"The date must be unique"),
    ]


class StockPickingDrive(models.Model):
    _name = "stock.picking.router.drive"
    _description = 'Drive config'

    name = fields.Many2one(comodel_name='res.partner', string='Driver')
    driver_id = fields.Many2many(comodel_name='stock.picking.router',
                                 string='Routers')
    qty = fields.Integer(string='Qty', default=0)
