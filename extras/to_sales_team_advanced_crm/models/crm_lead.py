from odoo import models, fields, api
from odoo.addons.crm.models import crm_lead

CRM_LEAD_FIELDS_TO_MERGE = crm_lead.CRM_LEAD_FIELDS_TO_MERGE + [
    'team_leader_id',
    'regional_manager_id',
    'crm_team_region_id'
    ]


class Lead(models.Model):
    _inherit = "crm.lead"

    team_leader_id = fields.Many2one('res.users', string='Team Leader', compute='_compute_team_id', store=True)
    regional_manager_id = fields.Many2one('res.users', string='Regional Manager', compute='_compute_team_id', store=True)
    crm_team_region_id = fields.Many2one('crm.team.region', string='Sales Region', compute='_compute_team_id', store=True)

    @api.depends('team_id')
    def _compute_team_id(self):
        for r in self:
            team_id = r.team_id
            vals = {}
            vals['crm_team_region_id'] = team_id.crm_team_region_id.id
            vals['regional_manager_id'] = team_id.regional_manager_id.id
            vals['team_leader_id'] = team_id.user_id.id
            r.update(vals)