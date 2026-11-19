# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json
import pytz
import logging

from datetime import datetime
from psycopg2 import IntegrityError

from odoo import http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.translate import _
from odoo.exceptions import ValidationError
from odoo.addons.base.models.ir_qweb_fields import nl2br
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
_logger = logging.getLogger(__name__)


class CpeDescarga(http.Controller):

    @http.route('/cpe/download_report/<int:ids>', methods=['GET'], type='http', auth="public")
    @serialize_exception
    def download_cpe_document(self, ids=None, **kw):
        account_id  = http.request.env['account.move'].sudo().search([('id', '=', ids )])
        if account_id.pe_cpe_id:
            filename = str(account_id.pe_cpe_id.name) +".xml"
            xml_file = base64.b64decode(account_id.pe_cpe_id.datas or '')
        elif account_id.binary_version:
            filename = str(account_id.ref) +".xml"
            xml_file = base64.b64decode(account_id.binary_version or '')
        else:
            return request.not_found()
        return request.make_response(xml_file, [('Content-Type', 'application/octet-stream'),('Content-Disposition', content_disposition(filename))])