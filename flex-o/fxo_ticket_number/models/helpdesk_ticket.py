# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError

class HelpdeskTicket(models.Model):
	_inherit = 'helpdesk.ticket'

	seq_compute = fields.Char(compute='_compute_seq', store=True)
	seq = fields.Char()

	@api.model
	def create(self, vals):
		res = super(HelpdeskTicket, self).create(vals)
		res.seq = self.env['ir.sequence'].next_by_code('helpdesk_ticket_code') or ''
		return res

	@api.depends('name', 'seq')
	def _compute_seq(self):
		for record in self:
			seq = record.seq if record.seq else ''
			name = record.name if record.name else ''
			record.seq_compute = seq + ' ' + name