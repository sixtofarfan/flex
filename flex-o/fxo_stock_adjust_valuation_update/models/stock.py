# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory'

    def update_cost(self):
        for item in self.line_ids:
            item._check_initial_cost()


class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    @api.constrains('initial_cost')
    def _check_initial_cost(self):
        move = self.env['stock.move'].search([
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.company_id.id),
            # ('location_id','=',self.location_id.id),
            ('inventory_id', '=', self.inventory_id.id),
            ('product_uom_qty', '=', self.product_qty)

        ])
        if len(move) > 0:
            move_ids = [m.id for m in move]
            valuation_layer = self.env['stock.valuation.layer'].search([
                ('stock_move_id', 'in', move_ids),
            ])
            for value in valuation_layer:
                value.unit_cost = self.initial_cost
