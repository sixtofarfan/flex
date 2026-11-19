# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class res_users(models.Model):
	_inherit = 'res.users'

	project_number = fields.Integer('Project Number',compute="get_project_number")

	def get_project_number(self):
		for i in self:
			n = self.env['project.project'].search([('user_id','=',i.id)])
			cant = 0
			for pro in n:
				tasks = self.env['project.task'].search([('project_id','=',pro.id)])
				flag = True
				for tarea in tasks:
					if tarea.is_closed:
						pass
					else:
						flag = False
				if flag:
					cant+=1
			i.project_number = cant