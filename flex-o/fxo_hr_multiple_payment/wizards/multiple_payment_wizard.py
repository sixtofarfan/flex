# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class MultiplePaymentWizard(models.TransientModel):
	_inherit = 'multiple.payment.wizard'

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

	def verify_bbva_cts_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bbva.cts'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if not Partner:
				log += 'El empleado %s no tiene un partner asociado \n' % move.employee_id.name
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago \n' % move.employee_id.name
			if not Partner.type_document_id.bbva_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BBVA\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.cts_bank_account_id:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.employee_id.name
			Account = self.get_account(move, 'bbva', 'cts')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BCP ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if len(Account.acc_number) != 20 or Account.acc_number[:4] != '0011':
					log += 'El numero de cuenta %s del partner del documento %s no tiene el formato correcto\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bbva_cts_lines(self):
		Header = self.env['multiple.payment.bbva.cts'].browse(self._context.get('active_id'))
		self.verify_bbva_cts_move(self.cts_ids)
		for move in self.cts_ids:
			BankAccount = self.get_account(move, 'bbva', 'cts')
			Partner = move.employee_id
			self.env['multiple.payment.bbva.cts.line'].create({
				'bbva_cts_id': Header.id,
				'move_id': move.id,
				'partner_doc_type': Partner.type_document_id.bbva_code,
				'charge_type': 'I' if BankAccount.type_of_account == '3' else 'P',
				'partner_doc_number': Partner.identification_id,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': Partner.name,
				'amount': move.total_cts if Header.charge_currency_id.name == 'PEN' else move.cts_dollars,
				'alert_indicator': 'E',
				'alert_value': Partner.work_email if not Partner.work_email else '',
			})

	def verify_bbva_slip_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bbva.slip'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if not Partner:
				log += 'El empleado %s no tiene un partner asociado \n' % move.employee_id.name
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago \n' % move.employee_id.name
			if not Partner.type_document_id.bbva_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BBVA\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.cts_bank_account_id:
				log += 'El partner del documento %s no tiene cuentas bancarias agregadas\n' % move.employee_id.name
			Account = self.get_account(move, 'bbva', 'slip')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BCP ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if len(Account.acc_number) != 20 or Account.acc_number[:4] != '0011':
					log += 'El numero de cuenta %s del partner del documento %s no tiene el formato correcto\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bbva_slip_lines(self):
		Header = self.env['multiple.payment.bbva.slip'].browse(self._context.get('active_id'))
		self.verify_bbva_slip_move(self.slip_ids)
		for move in self.slip_ids:
			BankAccount = self.get_account(move, 'bbva', 'slip')
			Partner = move.employee_id
			self.env['multiple.payment.bbva.slip.line'].create({
				'bbva_slip_id': Header.id,
				'move_id': move.id,
				'partner_doc_type': Partner.type_document_id.bbva_code,
				'charge_type': 'I' if BankAccount.type_of_account == '3' else 'P',
				'partner_doc_number': Partner.identification_id,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': Partner.name,
				'amount': move.net_wage,
				'alert_indicator': 'E',
				'alert_value': Partner.work_email if not Partner.work_email else '',
			})

	def verify_bcp_cts_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bcp.cts'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not Partner.type_document_id.bcp_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BCP\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.cts_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta CTS agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'bcp', 'cts')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BCP ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if len(Account.acc_number) != 13:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bcp_cts_lines(self):
		Header = self.env['multiple.payment.bcp.cts'].browse(self._context.get('active_id'))
		self.verify_bcp_cts_move(self.cts_ids)
		for move in self.cts_ids:
			Partner = move.employee_id
			BankAccount = self.get_account(move, 'bcp', 'cts')
			self.env['multiple.payment.bcp.cts.line'].create({
				'bcp_cts_id': Header.id,
				'move_id': move.id,
				'payment_acc_number': BankAccount.acc_number,
				'partner_doc_type': Partner.type_document_id.bcp_code,
				'partner_doc_number': Partner.identification_id,
				'beneficiary_name': Partner.name,
				'amount': move.total_cts if Header.charge_currency_id.name == 'PEN' else move.cts_dollars,
			})

	def verify_bcp_slip_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.bcp.slip'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not Partner.type_document_id.bcp_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en BCP\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.wage_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta Haberes agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'bcp', 'slip')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en BCP ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if not Account.type_of_account:
					log += 'La cuenta %s no tiene un tipo de cuenta designado\n' % Account.acc_number
				if len(Account.acc_number) != 13:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_bcp_slip_lines(self):
		Header = self.env['multiple.payment.bcp.slip'].browse(self._context.get('active_id'))
		self.verify_bcp_slip_move(self.slip_ids)
		TYPES = ['C', 'A', ' ', 'B']
		for move in self.slip_ids:
			Partner = move.employee_id
			BankAccount = self.get_account(move, 'bcp', 'slip')
			self.env['multiple.payment.bcp.slip.line'].create({
				'bcp_slip_id': Header.id,
				'move_id': move.id,
				'account_type': TYPES[int(BankAccount.type_of_account)],
				'payment_acc_number': BankAccount.acc_number,
				'partner_doc_type': Partner.type_document_id.bcp_code,
				'partner_doc_number': Partner.identification_id,
				'beneficiary_name': Partner.name,
				'amount': move.net_wage,
			})

	def verify_interbank_cts_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.interbank.cts'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not Partner.type_document_id.interbank_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en Interbank\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.cts_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta bancaria CTS agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'interbank', 'cts')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en Interbank ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			if len(Account.acc_number) != 13:
				log += 'La cuenta de ahorros %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_interbank_cts_lines(self):
		Header = self.env['multiple.payment.interbank.cts'].browse(self._context.get('active_id'))
		self.verify_interbank_cts_move(self.cts_ids)
		for move in self.cts_ids:
			BankAccount = self.get_account(move, 'interbank', 'cts')
			Partner = move.employee_id
			self.env['multiple.payment.interbank.cts.line'].create({
				'interbank_cts_id': Header.id,
				'move_id': move.id,
				'partner_doc_type': Partner.type_document_id.interbank_code,
				'partner_doc_number': Partner.identification_id,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': Partner.name,
				'cell_phone': Partner.phone,
				'email': Partner.work_email,
				'amount': move.total_cts if Header.charge_currency_id.name == 'PEN' else move.cts_dollars,
				'amount_cts': move.contract_id.wage * 4,
			})

	def verify_interbank_slip_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.interbank.slip'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not Partner.type_document_id.interbank_code:
				log += 'El documento %s no tiene un tipo de documento del partner permitido en Interbank\n' % move.employee_id.name
			if not Partner.identification_id:
				log += 'El documento %s no tiene un numero de identificacion configurado en el partner\n' % move.employee_id.name
			if not move.employee_id.wage_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta bancaria CTS agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'interbank', 'slip')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas corrientes ni de ahorros en Interbank ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			if len(Account.acc_number) != 13:
				log += 'La cuenta de ahorros %s del partner del documento %s debe tener 13 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_interbank_slip_lines(self):
		Header = self.env['multiple.payment.interbank.slip'].browse(self._context.get('active_id'))
		self.verify_interbank_slip_move(self.slip_ids)
		for move in self.slip_ids:
			BankAccount = self.get_account(move, 'interbank', 'slip')
			Partner = move.employee_id
			self.env['multiple.payment.interbank.slip.line'].create({
				'interbank_slip_id': Header.id,
				'move_id': move.id,
				'partner_doc_type': Partner.type_document_id.interbank_code,
				'partner_doc_number': Partner.identification_id,
				'payment_acc_number': BankAccount.acc_number,
				'beneficiary_name': Partner.name,
				'cell_phone': Partner.phone,
				'email': Partner.work_email,
				'amount': move.net_wage,
			})

	def verify_scotiabank_cts_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.scotiabank.cts'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not move.employee_id.cts_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta bancaria CTS agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'scotiabank', 'cts')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas CTS en Scotiabank ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if not Account.type_of_account:
					log += 'La cuenta de CTS %s del partner del documento %s debe tener un Tipo de Cuenta Predefinido\n' % (Account.acc_number, move.employee_id.name)
				if Account.type_of_account in ['0', '1'] and len(Account.acc_number) != 10:
					log += 'La cuenta de CTS %s del partner del documento %s debe tener 10 digitos\n' % (Account.acc_number, move.employee_id.name)
				if Account.type_of_account == '3' and len(Account.acc_number) != 20:
					log += 'La cuenta corriente %s del partner del documento %s debe tener 20 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_scotiabank_cts_lines(self):
		Header = self.env['multiple.payment.scotiabank.cts'].browse(self._context.get('active_id'))
		self.verify_scotiabank_cts_move(self.cts_ids)
		for move in self.cts_ids:
			BankAccount = self.get_account(move, 'scotiabank', 'cts')
			self.env['multiple.payment.scotiabank.cts.line'].create({
				'scotiabank_cts_id': Header.id,
				'move_id': move.id,
				'payment_acc_number': BankAccount.acc_number if BankAccount.type_of_account in ['0', '1'] else '',
				'amount': move.total_cts if Header.charge_currency_id.name == 'PEN' else move.cts_dollars,
				'cci_acc_number': BankAccount.acc_number if BankAccount.type_of_account == '3' else '',
				'rem_amount': move.contract_id.wage,
			})

	def verify_scotiabank_slip_move(self, moves):
		log = ''
		Header = self.env['multiple.payment.scotiabank.slip'].browse(self._context.get('active_id'))
		for move in moves:
			Partner = move.employee_id
			if move in Header.line_ids.mapped('move_id'):
				log += 'El documento %s ya se ha agregado a este proceso de pago' % move.employee_id.name
			if not move.employee_id.wage_bank_account_id:
				log += 'El partner del documento %s no tiene cuenta bancaria Sueldo agregada\n' % move.employee_id.name
			Account = self.get_account(move, 'scotiabank', 'slip')
			if not Account:
				log += 'El partner del documento %s no tiene cuentas Sueldo en Scotiabank ni cuentas interbancarias en la moneda seleccionada\n' % move.employee_id.name
			else:
				if not Account.type_of_account:
					log += 'La cuenta de Sueldo %s del partner del documento %s debe tener un Tipo de Cuenta Predefinido\n' % (Account.acc_number, move.employee_id.name)
				if len(Account.acc_number) != 14:
					log += 'La cuenta de Sueldo %s del partner del documento %s debe tener 14 digitos\n' % (Account.acc_number, move.employee_id.name)
		if log:
			raise UserError('Ocurrieron los siguientes errores:\n' + log)

	def set_scotiabank_slip_lines(self):
		Header = self.env['multiple.payment.scotiabank.slip'].browse(self._context.get('active_id'))
		self.verify_scotiabank_slip_move(self.slip_ids)
		for move in self.slip_ids:
			Partner = move.employee_id
			BankAccount = self.get_account(move, 'scotiabank', 'slip')
			self.env['multiple.payment.scotiabank.slip.line'].create({
				'scotiabank_slip_id': Header.id,
				'move_id': move.id,
				'employee_code': Partner.identification_id,
				'employee_name': Partner.name,
				'amount1': move.net_wage,
				'account': BankAccount.acc_number,
			})