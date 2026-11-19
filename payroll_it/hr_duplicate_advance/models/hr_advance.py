# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrAdvance(models.Model):
	_inherit = 'hr.advance'

	def duplicate_custom(self):
		wizard = self.env['hr.advance.duplicate'].create({})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'hr.advance.duplicate',
			'views': [[False, 'form']],
			'target': 'new',
			'context': {'advances_ids': self.ids}
		}


class HrAdvanceDuplicate(models.TransientModel):
	_name = 'hr.advance.duplicate'
	_description = 'Duplicar adelantos'

	date_advance = fields.Date('Fecha de adelanto')
	date_payment = fields.Date('Fecha de Descuento')

	def make_advances(self):
		advances_act = self.env['hr.advance'].browse(self.env.context.get('advances_ids'))
		for l in advances_act:
			a = l.copy(default=None)
			a.date=self.date_advance
			a.discount_date = self.date_payment
			a.state='not payed'




