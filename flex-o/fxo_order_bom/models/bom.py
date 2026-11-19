# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class SaleOrderBom(models.Model):
    _name = "sale.order.bom"

    name =  fields.Date(string='Fecha')

    sale_bom_line_id = fields.One2many(comodel_name='sale.order.bom.line', inverse_name='sale_bom_id', string='BOM line')

    picking_id = fields.Many2many(comodel_name='stock.picking',
                                  compute='compute_field_picking_id',
                                  string='BOM line')


    @api.model
    def compute_field_picking_id(self):
        for item in self:
            date = datetime.strptime(str(item.name), '%Y-%m-%d')
            item.picking_id = self.env['stock.picking']

            orders_id = self.env['sale.order'].search([
                ('commitment_date', '>=', date),
                ('commitment_date', '<=', date + timedelta(
                    hours=23, minutes=59, seconds=59, microseconds=999999))
            ])
            for order in orders_id:
                for line in order.order_line:
                    cant = len(line.product_id.bom_ids.bom_line_ids) 
                    if cant > 0: 
                        for bom in line.product_id.bom_ids.bom_line_ids:
                            product = self.env['sale.order.bom.line'].search([
                                    ('name', '=', bom.product_id.id),
                                    ('sale_bom_id', '=', item.id),
                                ])
                            if len(product) == 0 :
                                self.env['sale.order.bom.line'].create({
                                        'sale_bom_id':item.id,
                                        'name':bom.product_id.id,
                                        'qty': bom.product_qty
                                    })
                            else :
                                product.qty += bom.product_qty
                    else :
                        product = self.env['sale.order.bom.line'].search([
                                    ('name', '=', line.product_id.id),
                                    ('sale_bom_id', '=', item.id),
                                ])
                        if len(product) == 0 :
                            self.env['sale.order.bom.line'].create({
                                        'sale_bom_id':item.id,
                                        'name':line.product_id.id,
                                        'qty': line.product_uom_qty
                                    })
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')],
                             string='State',
                             default='draft')


class SaleOrderBomLine(models.Model):
    _name = "sale.order.bom.line"

    name = fields.Many2one(comodel_name='product.product', string='Product')

    sale_bom_id = fields.Many2one(comodel_name='sale.order.bom',string='BOM')

    qty = fields.Float(string='Qty')

    """ qty = fields.Float(compute='_compute_field_qty', string='Qty')

    @api.model
    def _compute_field_qty(self):
        for item in self:
            item.qty = 0
            for stock in item.sale_bom_id.picking_id:
                product = self.env['stock.move'].search([
                    ('picking_id', '=', stock.id),
                    ('product_id', '=', item.name.id)
                ])
                for line in product:
                    item.qty += line.product_uom_qty - line.reserved_availability
 """