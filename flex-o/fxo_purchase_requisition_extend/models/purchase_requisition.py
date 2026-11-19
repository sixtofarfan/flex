# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr
from datetime import datetime, time

_logger = logging.getLogger(__name__)

class PurchaseRequisitionLine(models.Model):
    _inherit = 'purchase.requisition.line'

    description = fields.Text(string='Description')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.description = ''
        if self.product_id.id:
            self.description = self.product_id.name
    
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        res = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name, product_qty, price_unit, taxes_ids)
        res['move_dest_ids'] = self.move_dest_id and [(4, self.move_dest_id.id)] or []
        res['name'] = self.description
        return res