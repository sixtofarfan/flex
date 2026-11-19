# -*- coding: utf-8 -*-
from odoo  import models, fields, api
from odoo.exceptions import UserError

class MoveLineDescriptionWizard(models.TransientModel):
	_name = 'move.line.description.wizard'

	name = fields.Char(string='Descripcion', required=True)

	def set_description(self):
		MoveLine = self.env['account.move.line'].browse(self._context.get('active_id'))
		MoveLine.name = self.name