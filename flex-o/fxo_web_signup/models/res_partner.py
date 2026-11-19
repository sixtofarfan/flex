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


class Partner(models.Model):
    _inherit = 'res.partner'

    document  = fields.Char(string='Document')

    # @api.constrains('document')
    # def set_document_ve(self):
    #     self.document_number = self.document