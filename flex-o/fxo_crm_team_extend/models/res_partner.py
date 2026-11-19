# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    debt_collector_id  = fields.Many2one(comodel_name='res.users', string='Debt Collector')
    