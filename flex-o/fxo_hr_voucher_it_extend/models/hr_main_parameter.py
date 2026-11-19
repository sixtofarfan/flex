# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	signature_width = fields.Float(string='Ancho de Firma', default=160.0)
	signature_height = fields.Float(string='Alto de Firma', default=35.0)