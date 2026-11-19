# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountReconcileModel(models.Model):
	_inherit = 'account.reconcile.model'

	def _prepare_reconciliation(self, st_line, move_lines=None, partner=None):
		data = super(AccountReconcileModel,self)._prepare_reconciliation(st_line, move_lines, partner)
		if move_lines:
			for aml_dict in data['counterpart_aml_dicts']:
				if aml_dict['move_line'].type_document_id:
					aml_dict['type_document_id'] = aml_dict['move_line'].type_document_id.id
				if aml_dict['move_line'].nro_comp:
					aml_dict['nro_comp'] = aml_dict['move_line'].nro_comp

		return data