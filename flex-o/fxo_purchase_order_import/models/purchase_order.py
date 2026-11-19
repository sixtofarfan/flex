# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	search_company = fields.Many2one('res.company', string='Compañia de Busqueda')
	project_log_id = fields.Many2one('project.log', string='Proyecto')

	def get_wizard_import(self):
		if not self.search_company:
			raise UserError('Debe seleccionar una compañia de busqueda')
		Materials = self.env['material.plan'].search([
			('partner_id', '=', self.partner_id.id), 
			('state', '=', 'in_progress'),
			('company_id', '=', self.search_company.id)
		])
		context = self._context.copy()
		context.update({'default_material_plan_ids': Materials.ids})
		return {
			'name': 'Importacion Lineas',
			'type': 'ir.actions.act_window',
			'res_model': 'purchase.order.line.import',
			'views': [(False, 'form')],
			'context': context,
			'target': 'new',
		}