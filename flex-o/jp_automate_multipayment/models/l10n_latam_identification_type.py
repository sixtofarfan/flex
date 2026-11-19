# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields

class L10nLatamIdentificationType(models.Model):
	_inherit = "l10n_latam.identification.type"

	bbva_code = fields.Char()
	bcp_code = fields.Char()
	interbank_code = fields.Char()