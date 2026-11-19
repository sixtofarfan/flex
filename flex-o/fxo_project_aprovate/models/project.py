# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class ProjectTask(models.Model):
    _inherit = "project.task"

    is_template = fields.Boolean(string=' Is Template')

    is_move_stage_task = fields.Boolean(
        string='Move the next task to the next immediate stage')


    is_begin_end_task = fields.Selection([
        ('start', 'Start'),
        ('end','End'),
        ('none','None'),
        ],
        string='Start and End Task Indicator')

    start_days = fields.Integer(string='Start days after completion of previous task')
    term_days  = fields.Integer(string='Days of homework duration')
