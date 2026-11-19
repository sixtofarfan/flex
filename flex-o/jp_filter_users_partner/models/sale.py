# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
	_inherit = 'res.partner'

	user_ids = fields.Many2many('res.users','partner_users_filter_rel','partner_id','user_id','Usuarios Acceso')

	admin_filter = fields.Boolean('Admin Filter',compute="get_admin_filter")

	def get_admin_filter(self):
		flag = False
		if self.env.uid in self.env.ref('jp_filter_users_partner.venta_filtrado_acceso_administrator').users.ids:
			flag = True
		for i in self:			
			i.admin_filter = flag

	def get_contacts(self):
		t = {
			'type': 'ir.actions.act_window',
			'name': 'Contactos',
			'res_model': 'res.partner',
			'view_mode': 'kanban,tree,form,activity',
			'context':{'default_is_company': True},
		}
		if self.env.uid in self.env.ref('jp_filter_users_partner.venta_filtrado_acceso_administrator').users.ids:
			pass
		else:
			t['domain']=[('user_ids', 'in', self.env.uid)]
		return t


class ResUsers(models.Model):
	_inherit = 'res.users'

	partner_ids = fields.Many2many('res.partner','partner_users_filter_rel','user_id','partner_id','Contactos Acceso')
