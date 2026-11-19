# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ResPartner(models.Model):
	_inherit = 'res.partner'

	def _get_status(self):
		bt_obj = self.env['base.element']
		return bt_obj.get_as_selection('STATUS.PARTNER')

	status_id = fields.Selection(_get_status, "Estado Cliente")
	#status_id = fields.Many2one('base.element', string="Estado Cliente", domain=[('table_id.code', '=', 'STATUS.PARTNER')])

