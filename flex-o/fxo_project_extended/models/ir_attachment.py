# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class IrAttachment(models.Model):
	_inherit = 'ir.attachment'

	@api.model
	def create(self, vals):
		if self._context.get('from_project'):
			raise UserError('No se puede crear registros desde esta vista')
		return super(IrAttachment, self).create(vals)

	def write(self, vals):
		if self._context.get('from_project'):
			raise UserError('No se puede modificar registros desde esta vista')
		return super(IrAttachment, self).write(vals)