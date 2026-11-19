# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat, float_repr


from datetime import datetime
from lxml import etree
from PyPDF2 import PdfFileReader
from collections import namedtuple

import io
import base64


class AccountMove(models.Model):
    _inherit = "account.move"
    _name = "account.move"

    is_cpe_import = fields.Boolean(string='Is CPE imported?', default = False)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _name = "account.move.line"

    is_cpe_import = fields.Boolean(string='Is CPE imported?', default = False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.is_cpe_import:
            return
        else:
            res = super(AccountMoveLine, self)._onchange_product_id()
        return res

