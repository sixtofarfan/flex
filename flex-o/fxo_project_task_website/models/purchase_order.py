# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    task_id = fields.Many2one('project.task', string='Task', related='custom_requisition_id.task_id')
    project_id = fields.Many2one('project.project', string='Project', related='task_id.project_id')
    project_status = fields.Many2one('project.status', string='Project State', related='project_id.project_status')
    is_closed = fields.Boolean(string="Is Closed Status", related='project_status.is_closed')