# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import UserError
from datetime import date, datetime
from calendar import monthrange

class ExportWizard(models.TransientModel):
	_name = 'export.wizard'
	_description = 'Export Wizard'

	from_date = fields.Date(string='Initial date', default=date.today().replace(day=1))
	to_date = fields.Date(string='End date', default=date.today().replace(day=monthrange(date.today().year, date.today().month)[1]))
	type_voucher = fields.Selection([
		('02', 'Sales'),
		('01', 'Purchases'),
		# ('other', 'Other'),
	], string='Type of voucher', default='sale')

	def get_export(self):
		if self.to_date < self.from_date:
			raise UserError(_('End date should be greather than initial date.'))
		return self.env.ref('jp_export_siscont.report_export_voucher_xlsx').report_action(self)
