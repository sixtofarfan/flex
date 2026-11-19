# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class MultiplePaymentWizard(models.TransientModel):
	_name = 'multiple.payment.wizard'
	_description = 'Multiple Payment Wizard'

	name = fields.Char()
	move_ids = fields.Many2many('account.move', 'multiple_payment_wizard_move_rel', string='Facturas', domain=[('type', '=', 'in_invoice'), ('state', '=', 'posted')])
	cts_ids = fields.Many2many('hr.cts.line', 'multiple_payment_wizard_cts_rel', string='CTS')
	slip_ids = fields.Many2many('hr.payslip', 'multiple_payment_wizard_slip_rel', string='Slips')

	def get_function(self):
		if self._context.get('bank_type') == 'bbva':
			return self.set_bbva_lines()
		elif self._context.get('bank_type') == 'bbva_cts':
			return self.set_bbva_cts_lines()
		elif self._context.get('bank_type') == 'bbva_slip':
			return self.set_bbva_slip_lines()
		elif self._context.get('bank_type') == 'bcp':
			return self.set_bcp_lines()
		elif self._context.get('bank_type') == 'bcp_cts':
			return self.set_bcp_cts_lines()
		elif self._context.get('bank_type') == 'bcp_slip':
			return self.set_bcp_slip_lines()
		elif self._context.get('bank_type') == 'interbank':
			return self.set_interbank_lines()
		elif self._context.get('bank_type') == 'interbank_cts':
			return self.set_interbank_cts_lines()
		elif self._context.get('bank_type') == 'interbank_slip':
			return self.set_interbank_slip_lines()
		elif self._context.get('bank_type') == 'scotiabank':
			return self.set_scotiabank_lines()
		elif self._context.get('bank_type') == 'scotiabank_cts':
			return self.set_scotiabank_cts_lines()
		else:
			return self.set_scotiabank_slip_lines()

	def get_account(self, move, type, mode=None):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if type == 'bbva':
			Header = self.env['multiple.payment.bbva'].browse(self._context.get('active_id'))
			if not MainParameter.bbva_bank:
				raise UserError('Falta configurar un Banco BBVA en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
			src_bank = MainParameter.bbva_bank
		elif type == 'bcp':
			Header = self.env['multiple.payment.bcp'].browse(self._context.get('active_id'))
			if not MainParameter.bcp_bank:
				raise UserError('Falta configurar un Banco BCP en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
			src_bank = MainParameter.bcp_bank
		elif type == 'interbank':
			Header = self.env['multiple.payment.interbank'].browse(self._context.get('active_id'))
			if not MainParameter.interbank_bank:
				raise UserError('Falta configurar un Banco Interbank en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
			src_bank = MainParameter.interbank_bank
		else:
			Header = self.env['multiple.payment.scotiabank'].browse(self._context.get('active_id'))
			if not MainParameter.scotiabank_bank:
				raise UserError('Falta configurar un Banco Scotiabank en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
			src_bank = MainParameter.scotiabank_bank
		if mode == 'cts':
			return move.employee_id.cts_bank_account_id
		elif mode == 'slip':
			return move.employee_id.wage_bank_account_id
		else:
			Partner = move.partner_id
		Current_Banks = Partner.bank_ids.filtered(lambda acc: acc.bank_id == src_bank and \
																   acc.type_of_account in ['0', '1'] and \
																   acc.currency_id == Header.charge_currency_id)
		CCI_Banks = Partner.bank_ids.filtered(lambda acc: acc.type_of_account == '3' and \
																  acc.currency_id == Header.charge_currency_id)
		if Current_Banks:
			Account = Current_Banks[0]
		elif not Current_Banks and CCI_Banks:
			Account = CCI_Banks[0]
		else:
			Account = None
		return Account

	def verify_bbva_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bbva'].browse(self._context.get('active_id'))
		for move in moves:
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.name
			if move.currency_id != Header.charge_currency_id:
				log += 'El documento %s tiene una moneda diferente a la moneda de la cuenta de cargo' % move.name
			if not move.partner_id.l10n_latam_identification_type_id.bbva_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BBVA\n' % move.name
			if not move.partner_id.vat:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.name
			if not move.type_document_id.bbva_code:
				log += 'El documento %s no tiene un tipo de documento permitido en BBVA\n' % move.name
			if not move.partner_id.bank_ids:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.name
			Account = self.get_account(move, 'bbva')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BBVA ni cuentas interbancarias en la moneda seleccionada\n' % move.name
			else:
				if len(Account.acc_number) != 20 or Account.acc_number[:4] != '0011':
					log += 'El numero de cuenta %s del partner del documento %s no tiene el formato correcto\n' % (Account.acc_number, move.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bbva_lines(self):
		Header = self.env['multiple.payment.bbva'].browse(self._context.get('active_id'))
		self.verify_bbva_move(self.move_ids)
		for move in self.move_ids:
			BankAccount = self.get_account(move, 'bbva')
			ref = move.ref.split('-')[1] if '-' in move.ref else move.ref
			self.env['multiple.payment.bbva.line'].create({
				'bbva_id': Header.id,
				'move_id': move.id,
				'partner_doc_type': move.partner_id.l10n_latam_identification_type_id.bbva_code,
				'charge_type': 'I' if BankAccount.type_of_account == '3' else 'P',
				'partner_doc_number': move.partner_id.vat,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': move.partner_id.name,
				'amount': move.amount_total,
				'doc_type': move.type_document_id.bbva_code,
				'doc_number': ref,
				'group_payment': 'N',
				'reference': move.glosa,
				'alert_indicator': 'E',
				'alert_value': move.partner_id.email if not move.partner_id.email else '',
			})

	def verify_bcp_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bcp'].browse(self._context.get('active_id'))
		for move in moves:
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.name
			if move.currency_id != Header.charge_currency_id:
				log += 'El documento %s tiene una moneda diferente a la moneda de la cuenta de cargo' % move.name
			if not move.partner_id.l10n_latam_identification_type_id.bcp_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BCP\n' % move.name
			if not move.partner_id.vat:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.name
			if not move.type_document_id.bcp_code:
				log += 'El documento %s no tiene un tipo de documento permitido en BCP\n' % move.name
			if not move.partner_id.bank_ids:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.name
			Account = self.get_account(move, 'bcp')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BCP ni cuentas interbancarias en la moneda seleccionada\n' % move.name
			else:
				if Account.type_of_account == '1' and len(Account.acc_number) != 14:
					log += 'La cuenta de ahorros %s del partner del documento %s debe tener 14 digitos\n' % (Account.acc_number, move.name)
				if Account.type_of_account == '0' and len(Account.acc_number) != 13:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.name)
				if Account.type_of_account == '3' and len(Account.acc_number) != 20:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 20 digitos\n' % (Account.acc_number, move.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bcp_lines(self):
		Header = self.env['multiple.payment.bcp'].browse(self._context.get('active_id'))
		self.verify_bcp_move(self.move_ids)
		ACCOUNT_TYPE = {'0': 'C', '1': 'A', '3': 'B'}
		for move in self.move_ids:
			BankAccount = self.get_account(move, 'bcp')
			ref = move.ref.split('-')[1] if '-' in move.ref else move.ref
			self.env['multiple.payment.bcp.line'].create({
				'bcp_id': Header.id,
				'move_id': move.id,
				'account_type': ACCOUNT_TYPE.get(BankAccount.type_of_account),
				'payment_type': '1',
				'partner_doc_type': move.partner_id.l10n_latam_identification_type_id.bcp_code,
				'partner_doc_number': move.partner_id.vat,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': move.partner_id.name,
				'beneficiary_ref': move.glosa,
				'company_ref': '',
				'amount': move.amount_total,
				'flag': 'N',
				'doc_type': move.type_document_id.bbva_code,
				'doc_number': ref,
			})

	def verify_interbank_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.interbank'].browse(self._context.get('active_id'))
		for move in moves:
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.name
			if move.currency_id != Header.charge_currency_id:
				log += 'El documento %s tiene una moneda diferente a la moneda de la cuenta de cargo' % move.name
			if not move.partner_id.l10n_latam_identification_type_id.interbank_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en Interbank\n' % move.name
			if not move.partner_id.vat:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.name
			if not move.type_document_id.interbank_code:
				log += 'El documento %s no tiene un tipo de documento permitido en Interbank\n' % move.name
			if not move.partner_id.bank_ids:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.name
			Account = self.get_account(move, 'interbank')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en Interbank ni cuentas interbancarias en la moneda seleccionada\n' % move.name
			else:
				if Account.type_of_account in ['0', '1'] and len(Account.acc_number) != 13:
					log += 'La cuenta de ahorros %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.name)
				if Account.type_of_account == '3' and len(Account.acc_number) != 20:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 20 digitos\n' % (Account.acc_number, move.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_interbank_lines(self):
		Header = self.env['multiple.payment.interbank'].browse(self._context.get('active_id'))
		self.verify_interbank_move(self.move_ids)
		for move in self.move_ids:
			BankAccount = self.get_account(move, 'interbank')
			ref = move.ref.split('-')[1] if '-' in move.ref else move.ref
			self.env['multiple.payment.interbank.line'].create({
				'interbank_id': Header.id,
				'move_id': move.id,
				'charge_type': '99' if BankAccount.type_of_account == '3' else '09',
				'account_type': '' if BankAccount.type_of_account == '3' else ('001' if BankAccount.type_of_account == '0' else '002'),
				'partner_doc_type': move.partner_id.l10n_latam_identification_type_id.interbank_code,
				'partner_doc_number': move.partner_id.vat,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': move.partner_id.name,
				'cell_phone': move.partner_id.phone,
				'email': move.partner_id.email,
				'amount': move.amount_total,
				'doc_type': move.type_document_id.interbank_code,
				'doc_number': ref,
			})

	def verify_scotiabank_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.scotiabank'].browse(self._context.get('active_id'))
		for move in moves:
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.name
			if move.currency_id != Header.charge_currency_id:
				log += 'El documento %s tiene una moneda diferente a la moneda de la cuenta de cargo' % move.name
			if move.partner_id.l10n_latam_identification_type_id.name != 'RUC':
				log += 'El documento %s no tiene tipo de documento RUC\n' % move.name
			if not move.partner_id.vat:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.name
			if move.type_document_id.code != '01':
				log += 'El documento %s no tiene tipo de documento Factura\n' % move.name
			if not move.partner_id.bank_ids:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.name
			Account = self.get_account(move, 'scotiabank')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en Scotiabank ni cuentas interbancarias en la moneda seleccionada\n' % move.name
			else:
				if Account.type_of_account in ['0', '1'] and len(Account.acc_number) != 14:
					log += 'La cuenta de ahorros %s del partner del documento %s debe tener 14 digitos\n' % (Account.acc_number, move.name)
				if Account.type_of_account == '3' and len(Account.acc_number) != 20:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 20 digitos\n' % (Account.acc_number, move.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_scotiabank_lines(self):
		Header = self.env['multiple.payment.scotiabank'].browse(self._context.get('active_id'))
		self.verify_scotiabank_move(self.move_ids)
		for move in self.move_ids:
			BankAccount = self.get_account(move, 'scotiabank')
			ref = move.ref.split('-')[1] if '-' in move.ref else move.ref
			self.env['multiple.payment.scotiabank.line'].create({
				'scotiabank_id': Header.id,
				'move_id': move.id,
				'partner_doc_number': move.partner_id.vat,
				'beneficiary_name': move.partner_id.name,
				'email': move.partner_id.email,
				'doc_number': ref,
				'amount': move.amount_total,
				'payment_type': '' if BankAccount.type_of_account == '3' else ('2' if BankAccount.type_of_account == '0' else '3'),
				'payment_acc_number': '' if BankAccount.type_of_account == '3' else BankAccount.acc_number,
				'payment_inter_acc_number': BankAccount.acc_number if BankAccount.type_of_account == '3' else '',
			})