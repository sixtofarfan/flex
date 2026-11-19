# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleSubscriptionLineState(models.Model):
	_inherit = 'sale.subscription.line.state'

	task_id = fields.Many2one('project.task')

	def set_confirm(self):
		res = super(SaleSubscriptionLineState, self).set_confirm()
		if self.task_id:
			Closed = self.env['project.status'].search([('is_closed', '=', True)])[0]
			if not Closed:
				raise UserError('No se ha encontrado una etapa con check Cerrado marcado defina una para continuar')
			self.task_id.project_id.date_end = self.date
			self.task_id.project_id.project_status = Closed.id
			self.task_id.project_id.project_state = 'done'
			self.task_id.project_id.date_state = fields.Datetime.now()
		return res

	def set_draft(self):
		res = super(SaleSubscriptionLineState, self).set_draft()
		if self.task_id:
			self.task_id.project_id.date_end = None
			self.task_id.project_id.project_state = 'created'
			self.task_id.project_id.date_state = fields.Datetime.now()
		return res