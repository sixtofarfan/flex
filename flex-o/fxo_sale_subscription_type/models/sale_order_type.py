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

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('none', 'None')]

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
    _inherit = 'sale.order.type'

    has_date_update_from = fields.Selection(CATEGORY_SELECTION,
                                            string="Has Date From",
                                            default="none",
                                            required=True)

    has_date_update_to = fields.Selection(CATEGORY_SELECTION,
                                          string="Has Date to",
                                          default="none",
                                          required=True)

    has_subscription_update_id = fields.Selection(CATEGORY_SELECTION,
                                                  string="Has Subscription",
                                                  default="none",
                                                  required=True)

    install_type = fields.Selection(string='Has Address', selection=[('required', 'Required'), ('none', 'None')],
                                    default="none")

    is_migration = fields.Boolean('Es Translado', default=False)

    change_state = fields.Selection([('done', 'Activo'), ('suspend', 'Suspendido')], 'Cambiar estado a')

    is_approval_required = fields.Boolean('Requiere Aprobacion', default=True)
    type_select = fields.Selection(TYPE_SELECTION, string="Tipo",
                                   default="none",
                                   required=True)
    has_signature_date = fields.Selection(CATEGORY_SELECTION,
                                          string="Has Signature Date",
                                          default="none",
                                          required=True)
    has_subscription_template_id = fields.Selection(CATEGORY_SELECTION,
                                                    string="Has Subscription Template",
                                                    default="none",
                                                    required=True)
