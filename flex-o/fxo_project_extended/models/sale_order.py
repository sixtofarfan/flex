# -*- coding: utf-8 -*-

import logging, base64

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from base64 import encodestring
from random import randrange

_logger = logging.getLogger(__name__)

class sale_order(models.Model):
	_inherit = 'sale.order'

	task_id_material = fields.Many2one('project.task','Tarea Material')

	def get_filtered_members(self, Destination, Team):
		Members = Team.mapped('members')
		Locations = self.env['wk.location.team'].search([('user_id', 'in', Members.ids)])
		State = Destination.state_id
		Province = Destination.province_id
		District = Destination.district_id
		if Destination.district_id:
			Fil_Members = Locations.filtered(lambda m: 
				Destination.state_id in m.state_ids \
				and Destination.province_id in m.province_ids \
				and Destination.district_id in m.district_ids
			)
		else:
			Fil_Members = Locations.filtered(lambda m: 
				Destination.state_id in m.state_ids \
				and Destination.province_id in m.province_ids \
			)
		return Fil_Members

	def get_balanced_members(self, Team):
		vals = []
		Members = Team.mapped('members')
		Ids = Members.ids
		for Id in Ids:
			Projects = self.env['project.task'].search([('user_id', '=', Id)])
			val = {'id': Id, 'quantity': len(Projects)}
			vals.append(val)
		minMember = min(vals, key=lambda v:v['quantity'])[0]
		return minMember

	def _action_confirm(self):
		res = super(sale_order, self)._action_confirm()
		for rec in self:
			for line in rec.order_line:
				seq = self.env['ir.sequence'].next_by_code('seq_project_service_id')
				if not seq:
					raise UserError('No existe una secuencia con el codigo seq_project_service_id')
				line.service_id_2 = seq
			for pro in rec.project_ids:
				pro.project_state = 'created'
				pro.date_state = fields.Datetime.now()
				Status = self.env['project.status'].search([('code', '=', 'start')])
				if not Status:
					raise UserError('No se ha encontrado un estado de proyecto con codigo start')
				pro.project_status = Status[0]
				if pro.sale_order_id and pro.sale_order_id.user_id and pro.sale_order_id.team_id:
					pro.salesman_id = pro.sale_order_id.user_id
					pro.salesman_team_id = pro.sale_order_id.team_id
				if pro.sale_line_id and pro.sale_line_id.partner_contact_id:
					pro.partner_contact_id = pro.sale_line_id.partner_contact_id
				if pro.partner_order_id:
					pro.partner_order_id = pro.partner_order_id.id
				if pro.sale_line_id:
					pro.service_id = pro.sale_line_id.service_id
				Destination = pro.sale_line_id.partner_street_destination
				Team = pro.wk_team_id
				Project = self.env['project.project'].search([('partner_id', '=', pro.partner_id.id), ('id', '!=', pro.id)])
				if Project and Project[0].user_id:
					pro.user_id = Project[0].user_id.id
				else:
					if Destination:
						Fil_Members = self.get_filtered_members(Destination, Team)
						if Fil_Members:
							pro.user_id = Fil_Members[0].user_id.id
							#raise UserError('No se encontro miembros en el equipo %s y el destino %s' % (Team.name, Destination.street))
					else:
						minMember = self.get_balanced_members(Team)
						if minMember:
							pro.user_id = minMember[0]
							#raise UserError('No se encontro miembros en el equipo %s' % Team.name)
				for task in pro.task_ids:
					if task.is_template:
						task.is_template = False
					if not task.user_id:
						Team = task.wk_team_id
						if Team.assign_method == 'randomly':
							Members = Team.mapped('members')
							Member = Members[randrange(len(Members))]
							task.user_id = Member.id
						if Team.assign_method == 'balanced':
							minMember = self.get_balanced_members(Team)
							task.user_id = minMember['id']
						if Team.assign_method == 'location':
							Destination = task.sale_line_id.partner_street_destination
							if Destination and Team:
								Fil_Members = self.get_filtered_members(Destination, Team)
								if Fil_Members:
									task.user_id = Fil_Members[0].user_id.id
		return res

	def action_confirm(self):
		for rec in self:
			for line in rec.order_line:
				seq = self.env['ir.sequence'].next_by_code('seq_project_service_id')
				if not seq:
					raise UserError('No existe una secuencia con el codigo seq_project_service_id')
				line.service_id_2 = seq
		res = super(sale_order, self).action_confirm()
		return res

	def action_quotation_send(self):
		res = super(sale_order, self).action_quotation_send()
		Tasks = self.project_id.task_ids.filtered(lambda t: t.type_task == '1')
		Planes = Tasks.mapped('plane_ids')
		attachment_ids, vals = [], {}
		for pla in Planes:
			attach = {}
			attach['name'] = '%s.docx' % pla.name
			attach['type'] = "binary"
			attach['datas'] = encodestring(pla.file)
			attach['res_model'] = "mail.compose.message"
			attachment_id = self.env['ir.attachment'].create(attach)
			attachment_ids.append(attachment_id.id)
		Template = self.env['mail.template'].browse(res['context']['default_template_id'])
		Template.attachment_ids = [(6, 0, attachment_ids)]
		return res

class sale_order_line(models.Model):
	_inherit = 'sale.order.line'

	def _timesheet_create_project(self):
		""" Generate project for the given so line, and link it.
			:param project: record of project.project in which the task should be created
			:return task: record of the created task
		"""
		self.ensure_one()
		account = self.order_id.analytic_account_id
		if not account:
			self.order_id._create_analytic_account(prefix=self.product_id.default_code or None)
			account = self.order_id.analytic_account_id

		# create the project or duplicate one     

		values = {
			'name': '%s - %s' % (self.order_id.client_order_ref, self.order_id.name) if self.order_id.client_order_ref else self.order_id.name,
			'analytic_account_id': False,
			'partner_id': self.partner_street_destination.parent_id.id if self.partner_street_destination.parent_id.id else  self.partner_street_destination.id,
			'location_id': self.partner_street_destination.id,
			'type_of_construction': 'other',
			'sale_line_id': self.id,
			'sale_order_id': self.order_id.id,
			'active': True,
			'company_id': self.company_id.id,
			'project_date': self.order_id.date_order,

		}
		if self.product_id.project_template_id:
			values['name'] = "%s - %s" % (values['name'], self.product_id.project_template_id.name)
			project = self.product_id.project_template_id.copy(values)
			project.tasks.write({
				'sale_line_id': self.id,
				'partner_id': self.order_id.partner_id.id,
				'email_from': self.order_id.partner_id.email,
			})
			# duplicating a project doesn't set the SO on sub-tasks
			project.tasks.filtered(lambda task: task.parent_id != False).write({
				'sale_line_id': self.id,
			})
		else:
			project = self.env['project.project'].create(values)

		# Avoid new tasks to go to 'Undefined Stage'
		if not project.type_ids:
			project.type_ids = self.env['project.task.type'].create({'name': _('New')})
		if not self.partner_street_destination:
			raise UserError('No se ha especificado un Partner Destino en la linea %s' % self.name)
		if not self.partner_street_destination.analytic_group_id.id:
			raise UserError( "El partner " + self.partner_street_destination.name + " no tiene un grupo analitico asignado.")
		if not self.partner_street_destination.analytic_group_id.sequence_id.id:
			raise UserError( "El Grupo Analitico " + self.partner_street_destination.analytic_group_id.name + " no tiene una secuencia asignada.")
		analytic_account_ibjh = self.env['account.analytic.account'].create({
			'name': project.name + (('-' + self.partner_street_destination.parent_id.name) if self.partner_street_destination.parent_id.id else '' ) + '-'+ self.partner_street_destination.name,
			'company_id': project.company_id.id,
			'partner_id': self.partner_street_destination.id,
			'active': True,
			'group_id': self.partner_street_destination.analytic_group_id.id,
			'code': self.partner_street_destination.analytic_group_id.sequence_id._next(),
			'a_debit': self.env['main.parameter'].search([])[0].a_debit_default.id,
			'a_credit':self.env['main.parameter'].search([])[0].a_credit_default.id,
		})   
		project.analytic_account_id = analytic_account_ibjh.id

		# link project as generated by current so line
		self.write({'project_id': project.id})
		return project
		
	def _timesheet_service_generation(self):

		""" For service lines, create the task or the project. If already exists, it simply links
			the existing one to the line.
			Note: If the SO was confirmed, cancelled, set to draft then confirmed, avoid creating a
			new project/task. This explains the searches on 'sale_line_id' on project/task. This also
			implied if so line of generated task has been modified, we may regenerate it.
		"""
		so_line_task_global_project = self.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking == 'task_global_project')
		so_line_new_project = self.filtered(lambda sol: sol.is_service and sol.product_id.service_tracking in ['project_only', 'task_in_project'])

		# search so lines from SO of current so lines having their project generated, in order to check if the current one can
		# create its own project, or reuse the one of its order.
		map_so_project = {}
		if so_line_new_project:
			order_ids = self.mapped('order_id').ids
			so_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '=', False)])
			map_so_project = {sol.order_id.id: sol.project_id for sol in so_lines_with_project}
			so_lines_with_project_templates = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.project_template_id', '!=', False)])
			map_so_project_templates = {(sol.order_id.id, sol.product_id.project_template_id.id): sol.project_id for sol in so_lines_with_project_templates}

		# search the global project of current SO lines, in which create their task
		map_sol_project = {}
		if so_line_task_global_project:
			map_sol_project = {sol.id: sol.product_id.with_context(force_company=sol.company_id.id).project_id for sol in so_line_task_global_project}

		def _can_create_project(sol):
			if not sol.project_id:
				return True
			return False

		def _determine_project(so_line):
			"""Determine the project for this sale order line.
			Rules are different based on the service_tracking:

			- 'project_only': the project_id can only come from the sale order line itself
			- 'task_in_project': the project_id comes from the sale order line only if no project_id was configured
			  on the parent sale order"""

			if so_line.product_id.service_tracking == 'project_only':
				return so_line.project_id
			elif so_line.product_id.service_tracking == 'task_in_project':
				return so_line.order_id.project_id or so_line.project_id

			return False

		# task_global_project: create task in global project
		for so_line in so_line_task_global_project:
			if not so_line.task_id:
				if map_sol_project.get(so_line.id):
					so_line._timesheet_create_task(project=map_sol_project[so_line.id])

		# project_only, task_in_project: create a new project, based or not on a template (1 per SO). May be create a task too.
		# if 'task_in_project' and project_id configured on SO, use that one instead
		for so_line in so_line_new_project:
			project = _determine_project(so_line)
			if not project and _can_create_project(so_line):
				project = so_line._timesheet_create_project()
				if so_line.product_id.project_template_id:
					map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)] = project
				else:
					map_so_project[so_line.order_id.id] = project
			elif not project:
				# Attach subsequent SO lines to the created project
				so_line.project_id = (
					map_so_project_templates.get((so_line.order_id.id, so_line.product_id.project_template_id.id))
					or map_so_project.get(so_line.order_id.id)
				)
			if so_line.product_id.service_tracking == 'task_in_project':
				if not project:
					if so_line.product_id.project_template_id:
						project = map_so_project_templates[(so_line.order_id.id, so_line.product_id.project_template_id.id)]
					else:
						project = map_so_project[so_line.order_id.id]
				if not so_line.task_id:
					so_line._timesheet_create_task(project=project)
