# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class PaymentOpWizard(models.TransientModel):
	_name = 'payment.op.wizard'
	_description = 'Payment Op Wizard'

	cash_number_op = fields.Char(string='Numero Operacion de Caja')

	def set_op_number(self):
		for pay in self.env['account.payment'].browse(self._context.get('active_ids')):
			pay.cash_nro_comp = self.cash_number_op