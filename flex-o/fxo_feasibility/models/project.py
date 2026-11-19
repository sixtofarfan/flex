# -*- coding: utf-8 -*-

from odoo import models, fields


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _create_analytic_account(self):
        for project in self:
            analytic_account = self.env["account.analytic.account"].create(
                {
                    "name": (project.partner_id.parent_id.name if project.partner_id.parent_id.id else "")
                            + ": Proyecto ("
                            + project.partner_id.name
                            + ")",
                    "company_id": project.company_id.id,
                    "partner_id": project.partner_id.id,
                    "active": True,
                }
            )
            project.write({"analytic_account_id": analytic_account.id})


class ProjectTask(models.Model):
    _inherit = 'project.task'

    type_id = fields.Many2one(
        related='project_id.type_id', string="Type", store=True
    )
