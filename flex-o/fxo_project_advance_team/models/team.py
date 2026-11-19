# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)


class WkTeam(models.Model):
    _inherit = 'wk.team'

    aprovate = fields.Boolean(string=' Requiere aprobacion')
    assign_method = fields.Selection(string='Metodo de Asignacion', selection=[
        ('manual', 'Manual'),
        ('random', 'Random'),
        ('balanced', 'Balanced'),
        ('location', 'Location'),
    ], default='location')
    approval_id = fields.Many2many(comodel_name='approval.category',
                                   string='Approval')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    wk_team_id = fields.Many2one(comodel_name='wk.team', string='Equipo de Proyecto')
    
