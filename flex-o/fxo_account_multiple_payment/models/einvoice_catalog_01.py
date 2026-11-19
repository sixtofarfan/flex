# -*- coding: utf-8 -*-

from odoo import models, fields, api

class EinvoiceCatalog01(models.Model):
	_inherit = 'einvoice.catalog.01'

	bbva_code = fields.Char()
	bcp_code = fields.Char()
	interbank_code = fields.Char()

	@api.model
	def set_bbva_codes(self):
		Documents = self.search([('code', 'in', ['01', '03', '07'])])
		for doc in Documents:
			if doc.code == '01':
				doc.bbva_code = 'F'
			if doc.code == '03':
				doc.bbva_code = 'B'
			if doc.code == '07':
				doc.bbva_code = 'N'

	@api.model
	def set_bcp_codes(self):
		Documents = self.search([('code', 'in', ['01', '07', '08'])])
		for doc in Documents:
			if doc.code == '01':
				doc.bcp_code = 'F'
			if doc.code == '07':
				doc.bcp_code = 'N'
			if doc.code == '08':
				doc.bcp_code = 'C'

	@api.model
	def set_interbank_codes(self):
		Documents = self.search([('code', 'in', ['01', '07', '08'])])
		for doc in Documents:
			if doc.code == '01':
				doc.interbank_code = 'F'
			if doc.code == '07':
				doc.interbank_code = 'C'
			if doc.code == '08':
				doc.interbank_code = 'D'