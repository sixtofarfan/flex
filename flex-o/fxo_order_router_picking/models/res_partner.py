# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class ResPartnet(models.Model):
    _inherit = "res.partner"

    router   = fields.Many2one(comodel_name='stock.picking.router',string='Router')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))

    router = fields.Many2one(related='partner_shipping_id.router')

    router_partner = fields.Many2one(comodel_name='res.partner',
                                     string='Driver')

    router_day = fields.Many2one(comodel_name='stock.picking.router.line',string=' Rourter Day')

    state_router = fields.Selection([
                                ('draft', 'Draft'),
                                ('confirm','Confirm'),
                                ('not deliver', 'Not Deliver'),
                                ('delivered', 'Delivered'),
                            ],
                            string='State',
                            default='draft')
    compute_name = fields.Many2one(comodel_name='sale.order',
                                   compute='_compute_name',
                                   string='Name')

    compute_partner_id = fields.Many2one(comodel_name='res.partner',
                                         compute='_compute_partner_id',
                                         string='Driver')

    @api.model
    def _compute_name(self):
        for item in self:
            item.compute_name = item.id

    @api.model
    def _compute_partner_id(self):
        for item in self:
            item.compute_partner_id = item.partner_id