from odoo import fields, models, api
from odoo.tools.translate import _
#import pudb


class RequireApproval(models.Model):
	_inherit = ['mail.thread']
	_name = "sale.order.approval"

	name = fields.Char(string='Nombre', copy=False)
	reason = fields.Char(string='Motivo', copy=False)
	date = fields.Date(string='Fecha', copy=False)
	state = fields.Selection([
		('detained', 'Retenido'),
		('refused', 'Rechazado'),
		('approved', 'Aprobado'),
	], string='Estado', readonly=True, copy=False, index=True, track_visibility='onchange')
	user_id = fields.Many2one('res.users', string='Usuario', index=True, track_visibility='onchange', default=lambda self: self.env.user)
	approval_id = fields.Many2one('sale.order', string='Order Reference', required=False, ondelete='cascade', index=True, copy=False)
	partner_id = fields.Many2one(related='approval_id.partner_id', string='Cliente', store=True)
	notes = fields.Text('Notes')

	def approve_line(self):
		self.ensure_one()
		self.write({'state': 'approved'})

	def deny_line(self):
		self.ensure_one()
		self.write({'state': 'refused'})

	def cancel_line(self):
		self.ensure_one()
		self.write({'state': 'detained'})
