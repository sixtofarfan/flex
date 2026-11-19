# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

class ApprovalRequest(models.Model):
	_inherit = "approval.request"

	request_credit_note_id = fields.Many2one('request.credit.note', string='Solicitud de Nota de Credito')
	has_cn_request = fields.Selection(related='category_id.has_cn_request')