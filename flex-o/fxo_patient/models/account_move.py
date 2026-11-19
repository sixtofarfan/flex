# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr



class AccountMove(models.Model):
	_inherit = 'account.move'

	patient_id = fields.Many2one(
		'res.partner',
		string='Paciente',
	)
	

