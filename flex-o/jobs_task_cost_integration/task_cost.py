# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import csv 
import json
import threading
from openerp.modules.registry import Registry 
from odoo import tools
import base64
import codecs
from datetime import datetime
from odoo.exceptions import UserError

class job_costing(models.Model):
	_inherit = 'job.costing'

	sale_order_line_ids = fields.One2many('sale.order.line',string='Costo Venta',compute='get_sale_order_line_ids')
	ganan_perd = fields.Float('Porc. de Ganancia/Perdida',compute="get_ganan_perd")

	def get_ganan_perd(self):
		for i in self:
			sum_order = 0
			for l in i.sale_order_line_ids:
				sum_order += l.price_unit
			if i.jobcost_total != 0:
				i.ganan_perd = ((sum_order / i.jobcost_total)-1.00)*100
			else:
				i.ganan_perd = 0



	def get_sale_order_line_ids(self):
		for i in self:
			i.sale_order_line_ids = i.project_id.sale_order_id.order_line.filtered(lambda r: r.partner_street_destination.id == i.partner_id.id)


class stock_picking(models.Model):
	_inherit = 'stock.picking'

	job_jp_project_id = fields.Many2one('project.project','Projecto')
	job_jp_task_id = fields.Many2one('project.task','Orden Trabajo')

class stock_move(models.Model):
	_inherit = 'stock.move'

	job_jp_project_id = fields.Many2one('project.project','Projecto')
	job_jp_task_id = fields.Many2one('project.task','Orden Trabajo')

class job_cost_line(models.Model):
	_inherit = 'job.cost.line'

	real_qty_consumed = fields.Float('Cantidad Real Consumida',compute="get_real_qty_consumed")
	cost_real_qty_consumed = fields.Float('Costo Real Consumido',compute="get_real_qty_consumed")
	price_sale = fields.Float('Precio Venta / Unidad', related='product_id.standard_price',store=True)

	def get_real_qty_consumed(self):
		for i in self:
			cant = 0
			price_unit_total = 0
			for inter in self.env['stock.move'].search([('task_id','=',i.direct_id.task_id.id),('product_id','=',i.product_id.id)]):
				cant += inter.quantity_done
				price_unit_cant = inter.quantity_done * inter.price_unit_it
			i.real_qty_consumed = cant
			i.cost_real_qty_consumed = price_unit_total

class material_plan(models.Model):
	_inherit = 'material.plan'

	job_cost_line_id = fields.Many2one('job.cost.line','Linea OT')

class material_purchase_requisition(models.Model):
	_inherit = 'material.purchase.requisition'

	
	@api.model
	def default_get(self, fields):
		rec = super(material_purchase_requisition, self).default_get(fields)
		if 'default_task_id' in self.env.context:
			tarea = self.env['project.task'].browse(self.env.context['default_task_id'])
			cont_g = []
			for i in tarea.material_plan_ids:
				cant = i.product_uom_qty
				linea_generate = self.env['material.purchase.requisition.line'].search([('requisition_id.task_id','=',tarea.id),('product_id','=',i.product_id.id)])
				for ant in linea_generate:
					cant -= ant.qty
				if cant>0:
					line = {
						'requisition_type': 'internal',
						'product_id':i.product_id.id,
						'description':i.description,
						'qty':cant,
						'uom':i.product_uom.id,
					}
					cont_g.append( (0,0,line) )
			rec['requisition_line_ids'] = cont_g
		return rec



class project_task(models.Model):
	_inherit = 'project.task'

	costing_id = fields.Many2one('job.costing','Hola de Costo')



	def view_stock_moves(self):
		result = self.env.ref('stock.stock_move_action')
		action_ref = result or False
		result = action_ref.read()[0]
		result['domain'] = str([('task_id', '=', self.id)])
		return result





	def generate_requisition_auto(self):	
		hr_user = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		if len(hr_user)>0:
			pass
		else:
			raise UserError( "No hay empleado registrado para el usuario conectado. Es requerido para la requisition de materiales.")
		hr_user = hr_user[0]
		if not hr_user.department_id.id:
			raise UserError( "El empleado registrado para el usuario actual no cuenta con un Departamento seleccionado. Es requerido para la requisition de materiales.")

		datos = {
			'employee_id': hr_user.id,
			'department_id': hr_user.department_id.id,
			'company_id': self.env.company.id,
			'project_id': self.project_id.id,
			'task_user_id': self.user_id.id,
			'task_id': self.id,
			'analytic_account_id': self.project_id.analytic_account_id.id,
			'request_date':fields.Date.today(),
		}
		t = self.env['material.purchase.requisition'].create(datos)
		for i in self.material_plan_ids:
			cant = i.product_uom_qty
			linea_generate = self.env['material.purchase.requisition.line'].search([('requisition_id.task_id','=',self.id),('product_id','=',i.product_id.id)])
			for ant in linea_generate:
				cant -= ant.qty
			if cant>0:
				line = {
					'requisition_type': 'internal',
					'product_id':i.product_id.id,
					'description':i.description,
					'qty':cant,
					'uom':i.product_uom.id,
					'requisition_id':t.id,
				}
				self.env['material.purchase.requisition.line'].create(line)
		return {
			'type': 'ir.actions.act_window',
			'name': 'Requisicion de Materiales',
			'view_mode': 'form',
			'res_model': 'material.purchase.requisition',
			'res_id': t.id,
		}

	def generate_requisition(self):	
		hr_user = self.env['hr.employee'].search([('user_id','=',self.env.uid)])
		if len(hr_user)>0:
			pass
		else:
			raise UserError( "No hay empleado registrado para el usuario conectado. Es requerido para la requisition de materiales.")
		hr_user = hr_user[0]
		if not hr_user.department_id.id:
			raise UserError( "El empleado registrado para el usuario actual no cuenta con un Departamento seleccionado. Es requerido para la requisition de materiales.")
		datos = {
			'default_employee_id': hr_user.id,
			'default_department_id': hr_user.department_id.id,
			'default_company_id': self.env.company.id,
			'default_project_id': self.project_id.id,
			'default_task_user_id': self.user_id.id,
			'default_task_id': self.id,
			'default_analytic_account_id': self.project_id.analytic_account_id.id,
			'default_request_date':fields.Date.today(),
		}
		cont_g = []
		for i in self.material_plan_ids:
			cant = i.product_uom_qty
			linea_generate = self.env['material.purchase.requisition.line'].search([('requisition_id.task_id','=',self.id),('product_id','=',i.product_id.id)])
			for ant in linea_generate:
				cant -= ant.qty
			if cant>0:
				line = {
					'requisition_type': 'internal',
					'product_id':i.product_id.id,
					'description':i.description,
					'qty':cant,
					'uom':i.product_uom.id,
				}
				cont_g.append( (0,0,line) )
		datos['default_requisition_line_ids'] = cont_g
		return {
			'type': 'ir.actions.act_window',
			'name': 'Requisicion de Materiales',
			'view_mode': 'tree,form',
			'res_model': 'material.purchase.requisition',
			'context': datos,
			'domain': [('task_id','=',self.id)],
		}

	def generate_cost(self):
		if self.costing_id.id == False:
			datos = {
				'name': self.project_id.name + ' - ' + self.name,
				'project_id': self.project_id.id,
				'analytic_id': self.project_id.analytic_account_id.id,
				'task_id': self.id,
				'partner_id': self.partner_id.id,
				'description':False,
				'so_number':False,
			}
			t = self.env['job.costing'].create(datos)
			self.costing_id = t.id

			for i in self.material_plan_ids:
				line = {
					'date': fields.Date.today(),
					'product_id':i.product_id.id,
					'description':i.description,
					'product_qty':i.product_uom_qty,
					'uom_id': i.product_uom.id,
					'cost_price': i.product_id.standard_price,
					'job_type':'material',
					'direct_id':t.id,
				}
				linea_obj = self.env['job.cost.line'].create(line)
				i.job_cost_line_id = linea_obj.id

			return {
				'type': 'ir.actions.act_window',
				'name': 'Hoja de OT',
				'view_mode': 'form',
				'res_model': 'job.costing',
				'res_id': t.id,
			}
		else:
			if self.costing_id.state == 'draft':
				for i in self.material_plan_ids:
					if i.job_cost_line_id.id:
						i.job_cost_line_id.product_id = i.product_id.id
						i.job_cost_line_id.description = i.description
						i.job_cost_line_id.product_qty = i.product_uom_qty
						i.job_cost_line_id.uom_id = i.product_uom.id
					else:
						line = {
							'date': fields.Date.today(),
							'product_id':i.product_id.id,
							'description':i.description,
							'product_qty':i.product_uom_qty,
							'uom_id': i.product_uom.id,
							'cost_price': i.product_id.standard_price,
							'job_type':'material',
							'direct_id':self.costing_id.id,
						}
						linea_obj = self.env['job.cost.line'].create(line)
						i.job_cost_line_id = linea_obj.id

			return {
				'type': 'ir.actions.act_window',
				'name': 'Hoja de OT',
				'view_mode': 'form',
				'res_model': 'job.costing',
				'res_id': self.costing_id.id,
			}



class MaterialPurchaseRequisition(models.Model):
	_inherit = 'material.purchase.requisition'


	@api.model
	def _prepare_pick_vals(self, line=False, stock_id=False):
		pick_vals = {
			'product_id' : line.product_id.id,
			'product_uom_qty' : line.qty,
			'product_uom' : line.uom.id,
			'location_id' : self.location_id.id,
			'location_dest_id' : self.dest_location_id.id,
			'name' : line.product_id.name,
			'picking_type_id' : self.custom_picking_type_id.id,
			'picking_id' : stock_id.id,
			'custom_requisition_line_id' : line.id,
			'company_id' : line.requisition_id.company_id.id,
			'job_jp_project_id': self.project_id.id,
			'job_jp_task_id': self.task_id.id,
		}
		return pick_vals

	@api.model
	def _prepare_po_line(self, line=False, purchase_order=False):
		res = super(MaterialPurchaseRequisition, self)._prepare_po_line(line, purchase_order)
		res['name'] = line.description
		res['partner_street_destination'] = line.requisition_id.task_id.project_id.location_id.id
		return res


	def request_stock(self):
		stock_obj = self.env['stock.picking']
		move_obj = self.env['stock.move']
		purchase_obj = self.env['purchase.order']
		purchase_line_obj = self.env['purchase.order.line']
		for rec in self:
			if not rec.requisition_line_ids:
				raise UserError(_('Please create some requisition lines.'))
			if any(line.requisition_type =='internal' for line in rec.requisition_line_ids):
				if not rec.location_id.id:
						raise UserError(_('Select Source location under the picking details.'))
				if not rec.custom_picking_type_id.id:
						raise UserError(_('Select Picking Type under the picking details.'))
				if not rec.dest_location_id:
					raise UserError(_('Select Destination location under the picking details.'))
				picking_vals = {
						'partner_id' : rec.employee_id.sudo().address_home_id.id,
						#'min_date' : fields.Date.today(),
						'location_id' : rec.location_id.id,
						'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
						'picking_type_id' : rec.custom_picking_type_id.id,#internal_obj.id,
						'note' : rec.reason,
						'custom_requisition_id' : rec.id,
						'origin' : rec.name,
						'company_id' : rec.company_id.id,
						'job_jp_project_id': rec.project_id.id,
						'job_jp_task_id': rec.task_id.id,                        
					}
				stock_id = stock_obj.sudo().create(picking_vals)
				delivery_vals = {
						'delivery_picking_id' : stock_id.id,
					}
				rec.write(delivery_vals)
				
			po_dict = {}
			for line in rec.requisition_line_ids:
				if line.requisition_type =='internal':
					pick_vals = rec._prepare_pick_vals(line, stock_id)
					move_id = move_obj.sudo().create(pick_vals)
				if line.requisition_type == 'purchase': #10/12/2019
					if not line.partner_id:
						raise UserError(_('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
					for partner in line.partner_id:
						if partner not in po_dict:
							po_vals = {
								'partner_id':partner.id,
								'currency_id':rec.env.user.company_id.currency_id.id,
								'date_order':fields.Date.today(),
								'company_id':rec.company_id.id,
								'custom_requisition_id':rec.id,
								'origin': rec.name,
							}
							purchase_order = purchase_obj.create(po_vals)
							po_dict.update({partner:purchase_order})
							po_line_vals = rec._prepare_po_line(line, purchase_order)
							purchase_line_obj.sudo().create(po_line_vals)
						else:
							purchase_order = po_dict.get(partner)
							po_line_vals = rec._prepare_po_line(line, purchase_order)
							purchase_line_obj.sudo().create(po_line_vals)
				rec.state = 'stock'