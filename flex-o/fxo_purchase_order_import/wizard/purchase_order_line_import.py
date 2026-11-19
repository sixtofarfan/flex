# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrderLineImport(models.TransientModel):
	_name = 'purchase.order.line.import'
	_description = 'Purchase Order Line Import'

	material_plan_ids = fields.Many2many('material.plan', 'purchase_line_import_rel')

	def import_order_lines(self):
		PurchaseOrder = self.env['purchase.order'].browse(self._context.get('active_id'))
		for mat in self.material_plan_ids:
			self.env['purchase.order.line'].create({
				'product_id': mat.product_id.id,
				'name': mat.description,
				'product_qty': mat.product_uom_qty,
				'product_uom': mat.product_uom.id,
				'order_id': PurchaseOrder.id,
			})
			mat.order_id = PurchaseOrder.id
			Log = self.env['project.log'].create({
				'name': mat.material_task_id.project_id.name,
				'code': mat.material_task_id.project_id.service_id,
				'partner_id': mat.material_task_id.project_id.partner_order_id.id,
			})
			PurchaseOrder.project_log_id = Log.id