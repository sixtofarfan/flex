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
TYPE_SELECTION = [
    ('adenda', 'Adenda'),
    ('renovation', 'Renovación'),
    ('upgrade', 'Upgrade'),
    ('upgrade_temp', 'Upgrade Temporal'),
    ('downgrade', 'Downgrade'),
    ('migration', 'Traslados'),
    ('none', 'None')
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    subscription_update_id = fields.Many2one(comodel_name='sale.subscription', string='Suscripcion')
    date_update_from = fields.Date(string='From')
    date_update_to = fields.Date(string='to')

    has_date_update_from = fields.Selection(related='type_id.has_date_update_from')
    has_date_update_to = fields.Selection(related='type_id.has_date_update_to')
    has_subscription_update_id = fields.Selection(related='type_id.has_subscription_update_id')
    has_signature_date = fields.Selection(related='type_id.has_signature_date')
    has_subscription_template_id = fields.Selection(related='type_id.has_subscription_template_id')
    save_suscripcion_to_duplicate = fields.Boolean(string="Guardar Suscripcion al duplicar")
    subscription_template_id = fields.Many2one('sale.subscription.template', string='Plantilla de contrato')
    signature_date = fields.Date(string='Fecha de firma')
    type_id_select = fields.Selection(related='type_id.type_select', store=True)

    def copy(self, default=None):
        t = super(SaleOrder, self).copy(default)
        # if self.save_suscripcion_to_duplicate:
        if 1 == 1:
            suscripciones = self.order_line.mapped('subscription_id')
            # raise ValueError(suscripciones)
            if suscripciones:
                t.subscription_update_id = suscripciones[0].id
        return t

    @api.onchange('subscription_update_id')
    def _onchange_subscription_template_id(self):
        if self.subscription_update_id:
            self.subscription_template_id = self.subscription_update_id.template_id.id
        else:
            self.subscription_template_id = None


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    subscription_update_id = fields.Many2one(comodel_name='sale.subscription')
    subscription_update_line_id = fields.Many2one(comodel_name='sale.subscription.line', string='Linea a Acualizar')
    date_update_from = fields.Date(related='order_id.date_update_from')
    date_update_to = fields.Date(related='order_id.date_update_to')
    type_id_select = fields.Selection(TYPE_SELECTION, string='Tipo Seleccionado', readonly=1)

    @api.onchange('order_id', 'product_id')
    def _onchange_type_id_select(self):
        self.type_id_select = self.order_id.type_id_select
