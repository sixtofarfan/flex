# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AccountDetractionsWizard(models.TransientModel):
	_inherit = 'account.detractions.wizard'

	# operation_type_id = fields.Many2one('einvoice.catalog.51', string='Tipo de Operacion')
	# #service_type_id = fields.Many2one('')
	# spot_percent = fields.Float(string='% SPOT')

	def generar(self):
		res = super(AccountDetractionsWizard, self).generar()
		invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
		invoice.move_detraccion_id.linked_to_detractions = invoice.linked_to_detractions
		invoice.move_detraccion_id.type_op_det 			 = invoice.type_op_det
		invoice.move_detraccion_id.type_operation 		 = invoice.type_operation.id
		invoice.move_detraccion_id.type_good_service	 = invoice.type_good_service.id
		invoice.move_detraccion_id.percent_detraction 	 = invoice.percent_detraction
		invoice.move_detraccion_id.date_detraccion		 = invoice.date_detraccion
		invoice.move_detraccion_id.code_operation		 = invoice.code_operation
		invoice.move_detraccion_id.voucher_number		 = invoice.voucher_number
		invoice.move_detraccion_id.detra_amount		     = invoice.detra_amount
		
 



		



