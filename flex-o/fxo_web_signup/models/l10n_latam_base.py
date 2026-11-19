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

class L10nLatamIdentificationType(models.Model):
    _inherit = 'l10n_latam.identification.type'

    is_portal = fields.Boolean(string='Mostrar en la Web')
    