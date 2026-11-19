# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.onchange('product_id')
    def _onchange_domain_lot_id(self):
        domain = [('product_id', '=', self.product_id.id), ('company_id', '=', self.company_id.id)]
        if self.product_id and self.picking_id.picking_type_id.code == 'outgoing':
            lot_ids = self._get_lot_ids(self.product_id.id, self.company_id.id)
            domain.append(('id', 'in', lot_ids))
        return {'domain': {'lot_id': domain}}

    def _get_lot_ids(self, product_id, company_id):
        lot_list = list()
        lot_ids = self.env['stock.production.lot'].search(
            [('product_id', '=', product_id), ('company_id', '=', company_id)])
        for lot in lot_ids:
            if lot.product_qty != 0:
                lot_list.append(lot.id)
        return lot_list
