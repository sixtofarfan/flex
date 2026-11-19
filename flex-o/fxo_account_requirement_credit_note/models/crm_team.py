# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrmTeam(models.Model):
	_inherit = 'crm.team'

	approval_credit_note_id = fields.Many2many('approval.category', 'crm_credit_note_rel')