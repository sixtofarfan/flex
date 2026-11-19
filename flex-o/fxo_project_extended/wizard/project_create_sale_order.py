# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectCreateSalesOrder(models.TransientModel):
    _inherit = 'project.create.sale.order'

    def _create_sale_order(self):
    	order = super(ProjectCreateSalesOrder, self)._create_sale_order()
    	Project = self.env['project.project'].browse(self._context.get('active_id'))
    	Child = None
    	if Project.partner_id.child_ids:
    		Child = Project.partner_id.child_ids[0].name
    	Names = order.order_line.mapped('product_id.name')
    	order.note = """
Proyecto: {0}
Cliente: {1}
Dirección de Instalación Cliente: {2}
Contacto del cliente: {3}
Telef. Contacto: {4}
Servicio a instalar: {5}
Service manager: {6}
Telef: {7}""".format(
			Project.name or '',
			Project.partner_id.name if Project.partner_id else '',
			Project.location_id.street if Project.location_id else '',
			Child.name if Child else '',
			Project.partner_id.mobile or '' if Project.partner_id else '',
			','.join(Names),
			Project.user_id.name or '' if Project.user_id else '',
			Project.user_id.mobile or '' if Project.user_id else '',
		)
    	return order