# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class HrTypeDocument(models.Model):
	_inherit = "hr.type.document"

	bbva_code = fields.Char()
	bcp_code = fields.Char()
	interbank_code = fields.Char()