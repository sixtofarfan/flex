# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	def name_get(self):
		result = []
		for record in self:
			result.append((record.id, '%s' % (record.move_id.ref or record.move_id.name)))
		return result

	@api.model
	def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
		args = args or []
		invoice_ids = []
		if name:
			invoice_ids = self._search(['|',('move_id.ref', '=', name),('move_id.name','=',name)] + args, limit=limit, access_rights_uid=name_get_uid)
		if not invoice_ids:
			invoice_ids = self._search(['|',('move_id.ref', operator, name),('move_id.name', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
		return self.browse(invoice_ids).name_get()