# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import content_disposition, request

MODELS = ('fxo.purchase.register.line', 'fxo.ledger.line')


class FxoDashboardExport(http.Controller):

    @http.route('/fxo_dashboards/export', type='http', auth='user', methods=['POST'])
    def export(self, model, fmt='xlsx', domain='[]', meta='{}', token=None, **kw):
        if model not in MODELS:
            return request.not_found()
        fmt = 'csv' if fmt == 'csv' else 'xlsx'
        filename, content, mimetype = request.env[model].fxo_export(fmt, json.loads(domain), json.loads(meta))
        response = request.make_response(content, headers=[
            ('Content-Type', mimetype),
            ('Content-Disposition', content_disposition(filename)),
        ])
        if token:
            response.set_cookie('fileToken', token)
        return response
