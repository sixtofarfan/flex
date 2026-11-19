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

_logger = logging.getLogger(__name__)

class project_conformity(models.Model):
	_name = 'project.conformity'

	name = fields.Char('Nombre')
	sequence = fields.Integer('Secuencia')
	comment = fields.Text('Comentarios')
	done_date = fields.Date('Fecha Finalizado')
	user_id = fields.Many2one('res.users','Usuario')
	conformity_date = fields.Date('Fecha Conformidad')
	project_task_id = fields.Many2one('project.task','Tarea')
	state = fields.Selection([('draft','Borrador'),('process','Proceso'),('done','Terminado')],'Estado',default='draft')
	partner_id = fields.Many2one('res.partner', string='Partner')
	order_id = fields.Many2one('purchase.order', string='OC')

	@api.onchange('order_id', 'state')
	def get_state(self):
		if self.state and self.order_id:
			self.order_id.task_state = self.state

class project_plane(models.Model):
	_name = 'project.plane'

	name = fields.Char('Nombre')
	sequence = fields.Integer('Secuencia')
	design_date = fields.Date('Fecha Diseño')
	notes = fields.Text('Notas')
	filename = fields.Char('Nombre Archivo')
	file = fields.Binary('Archivo',filename='filename')
	project_task_id = fields.Many2one('project.task','Tarea')
	analytic_account_id = fields.Many2one('account.analytic.account','Cuenta Analitica')
	state = fields.Selection([('draft','Borrador'),('process','Proceso'),('done','Terminado')],'Estado',default='draft')

	@api.model
	def create(self, vals):
		if self._context.get('from_project'):
			raise UserError('No se puede crear registros desde esta vista')
		return super(project_plane, self).create(vals)

class project_task(models.Model):
	_inherit = "project.task"

	type_task = fields.Selection([('1','Diseño'),('2','Planta Externa'),('3','Planta Interna'),('4','Ingenieria')],'Tipo Tarea',copy=True)
	plane_ids = fields.One2many('project.plane','project_task_id','Planos')
	material_ids = fields.One2many('sale.order','task_id_material','Materiales')
	contractor_ids = fields.One2many('purchase.order','task_id_contractor','Contratistas') 
	conformity_ids = fields.One2many('project.conformity','project_task_id','Conformidad')
	material_count = fields.Integer('Materiales',compute="get_material_count")
	othertask_count = fields.Integer('Otras Tareas',compute="get_othertask_count")
	addresses_id = fields.Many2one('sale.order.line.qty_street', related='sale_line_id.addresses_id', store=True)
	factibility_id = fields.Many2one('sale.order.line.factibility', related='sale_line_id.factibility_id', store=True)
	state_id = fields.Many2one('res.country.state', related='project_id.state_id', store=True, readonly=False)
	province_id = fields.Many2one('res.country.state', related='project_id.province_id', store=True, readonly=False)
	district_id = fields.Many2one('res.country.state', related='project_id.district_id', store=True, readonly=False)
	service_id = fields.Char(string='Service ID', related='project_id.service_id')
	project_picking_ids = fields.Many2many('material.purchase.requisition', 'material_purchase_task_rel', compute='get_project_picking_ids')
	project_attachment_ids = fields.Many2many('ir.attachment', 'project_attachment_rel', compute='get_project_attachment_ids')
	attachment_count = fields.Integer(compute='get_attachment_count')
	partner_street = fields.Char(related='partner_id.street')
	project_plane_ids = fields.Many2many('project.plane', 'project_task_plane_rel', compute='get_project_plane_ids')
	plane_count = fields.Integer(compute='get_plane_count')
	subscription_state_id = fields.One2many('sale.subscription.line.state', 'task_id', string='Actualizacion de Estado Servicio')
	partner_contact_id = fields.Many2one('res.partner', related='project_id.partner_contact_id', string='Contacto Cliente Proyecto')
	contact_email = fields.Char(related='partner_contact_id.email', string='Email')
	contact_mobile = fields.Char(related='partner_contact_id.mobile', string='Telefono')

	@api.onchange('stage_id')
	def verify_task_stage(self):
		#Function to verify changes in stage_id and get the next stage on the closest task
		if self.stage_id.closed:
			sql = """select sequence
from project_task
where project_id = {0}
order by sequence
			""".format(self.project_id.id)
			self._cr.execute(sql)
			data = self._cr.fetchall()
			aux = ''
			for e, d in enumerate(data):
				if int(d[0]) == self.sequence:
					aux = data[e + 1][0]
			Task = self.env['project.task'].search([('sequence', '=', aux), ('project_id', '=', self.project_id.id)])
			if Task.stage_id.sequence == 0:
				Stage = Task.next_stage()
				Task.stage_id = Stage
	
	def next_stage(self):
		#Function to get the next stage based on sequence field
		sql = """select sequence
from project_task_type
order by sequence
		"""
		self._cr.execute(sql)
		data = self._cr.fetchall()
		for e, d in enumerate(data):
			if int(d[0]) == self.stage_id.sequence:
				Stage = self.env['project.task.type'].search([('sequence', '=', data[e + 1][0])])
				if Stage:
					return Stage
				else:
					raise UserError('No se ha encontrado una Etapa siguiente para la etapa' % self.stage_id.name)

	@api.depends('project_plane_ids')
	def get_plane_count(self):
		for rec in self:
			rec.plane_count = len(rec.project_plane_ids)

	@api.depends('project_id', 'plane_ids')
	def get_project_plane_ids(self):
		for rec in self:
			Planes = rec.project_id.mapped('task_ids.plane_ids')
			rec.project_plane_ids = [(6, 0, Planes.ids)]

	@api.depends('project_attachment_ids')
	def get_attachment_count(self):
		for rec in self:
			rec.attachment_count = len(rec.project_attachment_ids)

	@api.depends('project_id', 'picking_ids')
	def get_project_picking_ids(self):
		for rec in self:
			Pickings = rec.project_id.mapped('task_ids.picking_ids')
			rec.project_picking_ids = [(6, 0, Pickings.ids)]

	def get_project_attachment_ids(self):
		for rec in self:
			Attachments = self.env['ir.attachment']
			for task in rec.project_id.task_ids:
				Attachments += self.env['ir.attachment'].search([('res_model', '=', 'project.task'), ('res_id', '=', task.id)])
			rec.project_attachment_ids = [(6, 0, Attachments.ids)]

	def send_email_gantt(self):
		for task in self.search([('stage_id.closed', '=', False)]):
			if task.planned_date_end and task.planned_date_begin and (fields.Date.today() - task.planned_date_end.date()).days > 0:
				for follower in task.message_follower_ids:
					if follower.partner_id.email:
						self.env['mail.mail'].create({
							'subject': 'Tarea no concluida en el plazo programado.',
							'body_html':'Cliente: %s'
										'Proyecto: %s'
										'Tarea: %s'
										'Fecha inicio: %s'
										'Fecha Fin: %s'
										'Etapa: %s' % (
											task.partner_id.name,
											task.project_id.name,
											task.name,
											task.planned_date_begin,
											task.planned_date_end,
											task.stage_id.name,
										),
							'email_to': follower.partner_id.email,
						}).send()

	def action_planes(self):
		context = self._context.copy()
		context.update({'from_project': True})
		return {
			'name': 'Planos',
			'type': 'ir.actions.act_window',
			'res_model': 'project.plane',
			'views': [(self.env.ref('fxo_project_extended.plane_tree_view').id, 'tree')],
			'domain': [('id', 'in', self.project_plane_ids.ids)],
			'context': context,
		}

	def action_attachments(self):
		context = self._context.copy()
		context.update({'from_project': True})
		return {
			'name': 'Archivos Adjuntos',
			'type': 'ir.actions.act_window',
			'res_model': 'ir.attachment',
			'views': [(self.env.ref('base.view_attachment_tree').id, 'tree')],
			'domain': [('id', 'in', self.project_attachment_ids.ids)],
			'context': context,
		}

	def action_subscription_state(self):
		if not self.env.user.has_group('fxo_project_extended.group_task_close'):
			raise UserError('Usted no tiene permisos para acceder a esta funcionalidad')
		ctx = {
			'name': 'Actualizar Estados de Servicio',
			'type': 'ir.actions.act_window',
			'res_model': 'sale.subscription.line.state',
			'views': [(False, 'form')],
			'context': self._context,
		}
		if self.subscription_state_id:
			ctx.update({'res_id': self.subscription_state_id[0].id})
		else:
			context = self._context.copy()
			SubLine = self.env['sale.subscription.line'].search([('service_id', '=', self.project_id.service_id)])
			if not SubLine:
				raise UserError('No se ha encontrado una linea de contrato con el mismo service_id que el proyecto %s' % self.project_id.name)
			context.update({
				'default_task_id': self.id,
				'default_partner_id': self.partner_id.id,
				'default_subscription_line_id': SubLine.id,
				'default_subscription_id': SubLine.analytic_account_id.id,
				'default_date': fields.Date.today(),
				'default_user_id': self.env.user.id,
			})
			ctx.update(({'context': context}))
		return ctx

	def get_othertask_count(self):
		for i in self:
			if i.project_id.id:
				i.othertask_count = len( self.env['project.task'].search([('project_id','=',i.project_id.id)]) )
			else:
				i.othertask_count = 0

	def get_data(self):
		t = {
			'type': 'ir.actions.act_window',
			'name': 'Tareas',
			'res_model': 'project.task',
			'view_mode': 'kanban,tree,form,calendar,pivot,graph,activity',
			'context': {'search_default_my_tasks': 1},
		}
		if self.env.uid in self.env.ref('fxo_project_extended.group_fxo_project_task_manager').users.ids:
			pass
		else:
			t['domain']=[('user_id', '=', self.env.uid)]
		return t
	# SFR no permite cambiar usuario
	#def write(self,vals):
		#for i in self:
			#if self.env.uid in self.env.ref('fxo_project_extended.group_fxo_project_task_user').users.ids:
				#if i.user_id.id != self.env.uid:
					#raise UserError( ("No puede editar otras tareas asignadas a otro personal."))
		#return super(project_task,self).write(vals)

	def open_other(self):
		if self.project_id.id:
			return {
				'name':'Tareas',
				'view_mode': 'tree,form',
				'res_model': 'project.task',
				'type': 'ir.actions.act_window',
				'domain': [('project_id','=',self.project_id.id)],
			}
		else:
			return

	def get_material_count(self):
		for i in self:
			i.material_count = len(i.material_ids)

	def action_materiales(self):
		return {
			'name': 'Materiales',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'sale.order',
			'type': 'ir.actions.act_window',
			'context': {'default_partner_id': self.partner_id.id,'default_partner_invoice_id': self.partner_id.id,'default_partner_shipping_id': self.partner_id.id},
		}

	def create_user(self):
		for i in self:
			if i.is_template:
				user_obj = False
				cant = 999999999
				for oj in i.wk_team_id.members:
					cant_t = len( self.env['project.task'].search([('id','!=',self.id),('user_id','=',oj.id),('is_template','=',False)]) )
					if cant_t < cant:
						user_obj = oj
				if user_obj != False:
					i.user_id = user_obj.id				

	@api.model
	def create(self,vals):
		t = super(project_task,self).create(vals)
		#t.create_user()
		return t

	# @api.onchange('stage_id')
	# def onchange_stage_id_other(self):
	# 	for i in self:
	# 		ant_task = self.env['project.task'].search([('project_id','=',i.project_id.id),('sequence','<',i.sequence),('is_closed','=',False)])
	# 		if len(ant_task)>0 :
	# 			raise UserError(_("Falta Terminar Tareas Anteriores"))

class Project_Project(models.Model):
	_inherit = 'project.project'

	date_localization = fields.Date(related='location_id.date_localization', readonly=False)
	partner_latitude = fields.Float(related='location_id.partner_latitude', readonly=False)
	partner_longitude = fields.Float(related='location_id.partner_longitude', readonly=False)
	state_id = fields.Many2one('res.country.state', related='location_id.state_id', store=True, readonly=False)
	country_id = fields.Many2one('res.country', related='location_id.country_id', store=True, readonly=False)
	province_id = fields.Many2one('res.country.state', related='location_id.province_id', store=True, readonly=False)
	district_id = fields.Many2one('res.country.state', related='location_id.district_id', store=True, readonly=False)
		# Fecha de inicio y Fin de Proyecto
	project_date = fields.Date(string='Fecha creacion')
	date_end = fields.Date(string='Fecha fin')
	partner_order_id = fields.Many2one('res.partner', string='Cliente del Pedido')
	service_id = fields.Char(string='Service ID')
	# Estado del Proyecto para control de Suspension (reactivate y done activan la facturacion)
	project_state = fields.Selection([
		('created', 'Creado'),
		('suspend', 'Suspendido'),
		('reactivate', 'Reactivado'),
		('done', 'Realizado'),
	], string='Estado', default='created')
	date_state = fields.Datetime(string='Fecha Estado', default=fields.Datetime.now())
	salesman_id = fields.Many2one('res.users', string='Vendedor')
	salesman_team_id = fields.Many2one('crm.team', string='Equipo de Ventas')
	# Team
	#sale_team_id = fields.Many2one('sale.order', related='sale_order.team_id', store=True, readonly=False, string='Equipo Ventas')
	partner_contact_id = fields.Many2one('res.partner', string='Contacto Cliente')
	contact_email = fields.Char(related='partner_contact_id.email', string='Email')
	contact_mobile = fields.Char(related='partner_contact_id.mobile', string='Telefono')

	@api.onchange('salesman_id')
	def get_salesman_team(self):
		if self.salesman_id and self.salesman_id.sale_team_id:
			self.salesman_team_id = self.salesman_id.sale_team_id

	@api.model
	def _map_tasks_default_valeus(self, task, project):
		""" get the default value for the copied task on project duplication """
		return {
			'stage_id': task.stage_id.id,
			'name': task.name,
			'company_id': project.company_id.id,
			'user_id': task.user_id.id,
		}

	@api.model
	def create_level_ids(self):
		for i in self:
			user_obj = False
			for oj in i.sale_order_id.team_id.user_project_manager_id.members:
				if oj.project_number <30 and oj.project_number < ( user_obj.project_number if user_obj != False else 9999999):
					user_obj = oj
			if user_obj != False:
				i.user_id = user_obj.id
			i.name = (i.sale_order_id.name if i.sale_order_id.name else '' ) + ( (' - ' + i.partner_id.name) if i.partner_id.name else ''  ) +  (i.sale_line_id.product_id.name if i.sale_line_id.id and i.sale_line_id.product_id.name else ''	)

	@api.model
	def create(self,vals):
		t = super(Project_Project,self).create(vals)
		if 'sale_order_id' in vals:
			t.create_level_ids()
		return t

	def write(self,vals):
		t = super(Project_Project,self).write(vals)
		if 'sale_order_id' in vals:
			self.create_level_ids()
		return t

	def get_data(self):
		t = {
			'type': 'ir.actions.act_window',
			'name': 'Proyectos',
			'res_model': 'project.project',
			'view_mode': 'kanban,form',
			'context': {'search_default_my_project_fxo': 1},
			'views': [
				[self.env.ref('project.view_project_kanban').id, 'kanban'],
				[self.env.ref('project.edit_project').id, 'form']
			]
		}
		if self.env.uid in self.env.ref('fxo_project_extended.group_fxo_project_manager').users.ids or self.env.uid in self.env.ref('fxo_project_extended.group_fxo_project_administrator').users.ids:
			pass
		else:
			t['domain']=[('user_id', '=', self.env.uid)]
		return t

	def generate_xls_template(self):
		import io
		from xlsxwriter.workbook import Workbook
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		ReportBase = self.env['report.base']
		if not MainParameter.dir_create_file:
			raise UserError('Falta configurar un directorio de descargas en Parametros Principales')
		route = MainParameter.dir_create_file
		workbook = Workbook(route + 'Plantilla Diseño de Planos.xlsx')
		workbook, formats = ReportBase.get_formats(workbook)

		import importlib
		import sys
		importlib.reload(sys)

		worksheet = workbook.add_worksheet("Plantilla")
		worksheet.set_tab_color('blue')

		HEADERS = ['ATTR ID', 'ID SERVICIO', 'NOMBRES', 'DIRECCION', 'TIPO LOCALIZACION', 'CIUDAD', 'LATITUD', 'LONGITUD']
		worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
		x = 1
		for rec in self:
			if rec.location_id:
				Location = rec.location_id
			else:
				Location = False
			if Location:
				if Location.type and Location.type != 'contact':
					street = Location.name
				else:
					street = Location.street
			else:
				street = ''
			worksheet.write(x, 0, rec.sale_order_id.name if rec.sale_order_id else '', formats['especial1'])
			worksheet.write(x, 1, rec.service_id if rec.service_id else '', formats['especial1'])
			worksheet.write(x, 2, rec.partner_id.name if rec.partner_id else '', formats['especial1'])
			worksheet.write(x, 3, street if street else '', formats['especial1'])
			worksheet.write(x, 4, Location.property_type if Location.property_type else '', formats['especial1'])
			worksheet.write(x, 5, Location.district_id.name if Location.district_id else '',formats['especial1'])
			worksheet.write(x, 6, Location.partner_latitude if Location.partner_latitude else '',formats['especial1'])
			worksheet.write(x, 7, Location.partner_longitude if Location.partner_longitude else '',formats['especial1'])
			x += 1

		widths = [12] * 8
		worksheet = ReportBase.resize_cells(worksheet, widths)
		workbook.close()

		f = open(route + 'Plantilla Diseño de Planos.xlsx', 'rb')
		return self.env['popup.it'].get_file('Plantilla Diseño de Planos.xlsx', base64.encodestring(b''.join(f.readlines())))

class ProjectType(models.Model):
	_inherit = 'project.type'

	is_design_project = fields.Boolean(string='Proyecto de Diseño', default=False)
