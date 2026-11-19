# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


CATEGORY_SELECTION = [
    ('required', 'Required'),
    ('optional', 'Optional'),
    ('no', 'None')]

class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    has_partner_request = fields.Selection(CATEGORY_SELECTION,
                                      string="Has Sale Order",
                                      default="no",
                                      required=True)

class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    permanence_id = fields.Many2one(comodel_name='crm.team.router.request', string='Permanence')
    has_partner_request = fields.Selection(related="category_id.has_partner_request")

    @api.constrains('request_status')
    def request_status_permanence_id(self):
        if self.permanence_id.id :
            self.permanence_id.update_state()