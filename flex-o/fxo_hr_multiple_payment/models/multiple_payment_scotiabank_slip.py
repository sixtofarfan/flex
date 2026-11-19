# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentScotiabankSlip(models.Model):
	_name = 'multiple.payment.scotiabank.slip'
	_description = 'Multiple Payment Scotiabank Slip'

	line_ids = fields.One2many('multiple.payment.scotiabank.slip.line', 'scotiabank_slip_id', states={'txt': [('readonly', True)]})
	charge_account_id = fields.Many2one('res.partner.bank', string='Cuenta de Cargo', required=True, states={'txt': [('readonly', True)]})
	charge_currency_id = fields.Many2one(related='charge_account_id.currency_id', string='Moneda de Cuenta de Cargo')
	institution_code = fields.Char(string='Codigo de Institucion', size=11, default=lambda self: self.env.company.vat if self.env.company.vat else '')
	state = fields.Selection([('draft', 'Borrador'),
							  ('txt', 'Txt Generado'),
							  ('payed', 'Pagado')], default='draft')

	@api.constrains('charge_account_id')
	def _get_acc_number(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter.scotiabank_bank:
			raise UserError('Falta configurar el un Banco Scotiabank en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
		for record in self:
			if record.charge_account_id.bank_id != MainParameter.scotiabank_bank:
				raise UserError('No se puede utilizar una cuenta bancaria diferente a Scotiabank')
			if len(record.charge_account_id.acc_number) != 14:
				raise UserError('La cuenta consta de 14 posiciones')

	@api.depends('line_ids')
	def _get_total_charge(self):
		for record in self:
			record.total_charge = sum(record.line_ids.mapped('amount')) if record.line_ids else 0

	def turn_txt(self):
		for record in self:
			record.state = 'txt'

	def turn_draft(self):
		for record in self:
			record.state = 'draft'

	def get_moves(self):
		wizard = self.env['multiple.payment.wizard'].create({'name': 'Facturas'})
		return {
			'type': 'ir.actions.act_window',
			'res_id': wizard.id,
			'view_mode': 'form',
			'res_model': 'multiple.payment.wizard',
			'views': [[False, 'form']],
			'context': self._context,
			'target': 'new',
		}

	def parse_number_txt(self, number, type, range):
		position = ''.join(range*['0'])
		if type == 'int':
			number = str(number)
			position = position[:-len(number)] + number
		if type == 'float':
			Lang = self.env['res.lang'].search([('active', '=', True)], limit=1)
			number = str(number).split(Lang.decimal_point)
			if len(number[1]) == 1:
				number[1] += '0'
			position = position[:-len(number[0] + number[1])] + number[0] + number[1]
		return position

	def get_scotiabank_slip_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sScotiabank CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			for line in record.line_ids:
				inst_aux = ' ' * 11
				bank_aux = ' ' * 10
				emp_code_aux = ' ' * 10
				emp_aux = ' ' * 30
				ref_aux = ' ' * 8
				f.write('{inst_code}{service_type}{bank_code}{emp_code}{emp_name}{situtation}{ref_code}\
{discount}{amount1}{amount2}{amount3}{amount4}{amount5}{amount6}{account}{blanks}{charge_mode}{charge_account}{emp_doc}\r\n'.format(
					inst_code = record.institution_code + inst_aux[len(record.institution_code):] if record.institution_code else inst_aux,
					service_type = '20' if record.charge_currency_id == 'PEN' else '21',
					bank_code = line.bank_code + bank_aux[len(line.bank_code):] if line.bank_code else bank_aux,
					emp_code = line.employee_code + emp_code_aux[len(line.employee_code):] if line.employee_code else emp_code_aux,
					emp_name = line.employee_name + emp_aux[len(line.employee_name):] if line.employee_name else emp_aux,
					situtation = line.situtation if line.situtation else ' ',
					ref_code = line.ref_code + ref_aux[len(line.ref_code):] if line.ref_code else ref_aux,
					discount = self.parse_number_txt(line.discount, 'float', 6) if line.discount else ' ' * 6,
					amount1 = self.parse_number_txt(line.amount1, 'float', 10) if line.amount1 else ' ' * 10,
					amount2 = self.parse_number_txt(line.amount2, 'float', 10) if line.amount2 else ' ' * 10,
					amount3 = self.parse_number_txt(line.amount3, 'float', 10) if line.amount3 else ' ' * 10,
					amount4 = self.parse_number_txt(line.amount4, 'float', 10) if line.amount4 else ' ' * 10,
					amount5 = self.parse_number_txt(line.amount5, 'float', 10) if line.amount5 else ' ' * 10,
					amount6 = self.parse_number_txt(line.amount6, 'float', 10) if line.amount6 else ' ' * 10,
					account = line.account if line.account else ' ' * 14,
					blanks = ' ' * 16,
					charge_mode = line.charge_mode if line.charge_mode else ' ',
					charge_account = record.charge_account_id.acc_number if record.charge_account_id else ' ' * 14,
					emp_doc = line.emp_doc if line.emp_doc else ' ' * 2,
					))
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Scotiabank CTS.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentScotiabankCTSLine(models.Model):
	_name = 'multiple.payment.scotiabank.slip.line'
	_description = 'Multiple Payment Scotiabank CTS Line'

	scotiabank_slip_id = fields.Many2one('multiple.payment.scotiabank.slip', ondelete='cascade')
	move_id = fields.Many2one('hr.payslip', string='Planillas', required=True)
	institution_code = fields.Char(string='Codigo de Institucion RUC', size=11)
	bank_code = fields.Char(string='Codigo de Banco', size=10)
	employee_code = fields.Char(string='Codigo de Empleado', size=10)
	employee_name = fields.Char(string='Nombre de Empleado', size=30)
	situtation = fields.Boolean(string='Situacion', default=True)
	ref_code = fields.Char(string='Codigo Referencial', size=8)
	discount = fields.Float(string='Porcentaje de Dscto.', digits=(7,2))
	amount1 = fields.Float(string='Monto 1', digits=(7,2))
	amount2 = fields.Float(string='Monto 2', digits=(7,2))
	amount3 = fields.Float(string='Monto 3', digits=(7,2))
	amount4 = fields.Float(string='Monto 4', digits=(7,2))
	amount5 = fields.Float(string='Monto 5', digits=(7,2))
	amount6 = fields.Float(string='Monto 6', digits=(7,2))
	account = fields.Char(string='Cuenta del Empleado', size=14)
	charge_mode = fields.Selection([
								('1', 'Cargo en Cuenta'),
								('5', 'Afiliado Planilla'),
								('6', 'Desafiliado Planilla'),
								('2', 'Cobro x cajero, ventanilla o Medios Virtuales'),
								], string='Modalidad de Cobro', default='1')
	emp_doc = fields.Selection([
								('01', 'DNI'),
								('02', 'Carnet Extranjeria'),
								('03', 'Carnet F.F.P.P.')
								], string='Tipo de Documento', default='01')
