# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr

_logger = logging.getLogger(__name__)


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    sale_update_id = fields.One2many(comodel_name='sale.order', inverse_name='subscription_update_id', string='Update')

    detail_id = fields.One2many(comodel_name='sale.subscription.update', inverse_name='subscription_id',
                                string='Detail', compute='_compute_currency_rate')
    signature_date = fields.Date(string='Fecha de firma', readonly=True)

    @api.onchange('date_start', 'template_id')
    def onchange_date_start(self):
        if self.date_start:
            periods = {'daily': 'days', 'weekly': 'weeks', 'monthly': 'months', 'yearly': 'years'}
            self.date = fields.Date.from_string(self.date_start) + relativedelta(**{
                periods[
                    self.recurring_rule_type]: self.template_id.recurring_rule_count * self.template_id.recurring_interval})


class SaleSubscriptionLine(models.Model):
    _inherit = 'sale.subscription.line'

    order_partner_street_id = fields.Many2one(related='analytic_account_id.partner_id', string='Partner')
    partner_street_destination = fields.Many2one(comodel_name='res.partner', string='Destination address')
    state = fields.Selection([('done', 'Activo'), ('suspend', 'Suspendido')], 'Estado', default='done')
    order_reference = fields.Char(string='Referencia del Pedido')


class SaleSubscriptionUpdate(models.Model):
    _name = 'sale.subscription.update'

    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    order_id = fields.Many2one(comodel_name='sale.order', string='Sale')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner')
    qty = fields.Integer(string='Qty')
    price_unit = fields.Float(string='Price Unit')
    price_subtotal = fields.Float(string='Sub total')
    date_update_from = fields.Date(string='From')
    date_update_to = fields.Date(string='to')
    subscription_id = fields.Many2one(comodel_name='sale.subscription', string='Subscription')


class SaleSubscriptionStage(models.Model):
    _inherit = 'sale.subscription.stage'

    code = fields.Char(string='Código',
                       help='Campo utilizado para poder filtrar los contratos por etapa, sin necesidad de hacerlo por '
                            'el campo nombre, los valores que se deben configurar deben quedar asi '
                            'Suspendido - (suspend), Baja - (cancel), Activo - (done), Borrador - (pending), Baja-adm - (cancel-adm)')
