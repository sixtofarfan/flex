# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]

class ApprovalCategory(models.Model):
	_inherit = "approval.category"

	has_cn_request = fields.Selection(CATEGORY_SELECTION, string='Nota de Credito', default='no', required=True)