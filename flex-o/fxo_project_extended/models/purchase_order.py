# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class purchase_order(models.Model):
	_inherit = 'purchase.order'

	task_id_contractor = fields.Many2one('project.task','Tarea Material')
	contractor_id = fields.Many2one('res.partner','Contratista')
	task_state = fields.Selection([
		('draft', 'Borrador'),
		('process', 'Proceso'),
		('done', 'Realizado'),
	], default='draft')