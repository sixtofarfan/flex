# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentBCP(models.Model):
	_name = 'multiple.payment.bcp'
	_description = 'Multiple Payment BCP'

	charge_account_id = fields.Many2one('res.partner.bank', string='Cuenta de Cargo', required=True, states={'txt': [('readonly', True)]}, domain=[('type_of_account', '=', '0')])
	charge_currency_id = fields.Many2one(related='charge_account_id.currency_id', string='Moneda de Cuenta de Cargo')
	total_charge = fields.Float(compute='_get_total_charge', string='Importe a Cargar', required=True, digits=(14, 2))
	process_date = fields.Date(string='Fecha de Proceso', states={'txt': [('readonly', True)]})
	reference = fields.Char(string='Referencia', size=25, states={'txt': [('readonly', True)]})
	flag = fields.Selection([
							('N', 'Cuando la cuenta de abono NO pertenece al mismo titular de la cuenta origen'),
							('S', 'Cuando la cuenta de abono SI pertenece al mismo titular de la cuenta origen')], default='N', string='Flag de exoneracion ITF')
	line_ids = fields.One2many('multiple.payment.bcp.line', 'bcp_id', states={'txt': [('readonly', True)]})
	state = fields.Selection([('draft', 'Borrador'),
							  ('txt', 'Txt Generado'),
							  ('payed', 'Pagado')], default='draft')

	def turn_txt(self):
		for record in self:
			record.state = 'txt'

	def turn_draft(self):
		for record in self:
			record.state = 'draft'

	@api.depends('line_ids')
	def _get_total_charge(self):
		for record in self:
			record.total_charge = sum(record.line_ids.mapped('amount')) if record.line_ids else 0

	@api.constrains('charge_account_id')
	def _get_acc_number(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter.bcp_bank:
			raise UserError('Falta configurar el un Banco BCP en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
		for record in self:
			if record.charge_account_id.bank_id != MainParameter.bcp_bank:
				raise UserError('No se puede utilizar una cuenta bancaria diferente a BCP')
			if len(record.charge_account_id.acc_number) != 13:
				raise UserError("""
Cuenta Corriente o Maestra consta de 13 posiciones.
Formato: SSSCCCCCCCMDD donde:
S=Número de Sucursal
C=Cuenta
M=Moneda (0: Soles / 1:Dólares)
D=Dígitos de control""")

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
			position = position[:-len(number[0] + '.' + number[1])] + number[0] + '.' + number[1]
		return position

	def get_bcp_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBCP.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			aux = '00'
			if record.process_date:
				year, month, day = str(record.process_date.year), str(record.process_date.month), str(record.process_date.day)
				process_date = year + aux[:-len(month)] + month + aux[:-len(day)] + day
			else:
				process_date = ' ' * 8
			aux_ref = ' ' * 40
			aux_account = ' ' * 20
			aux_check = '0' * 15
			acc_number = int(record.charge_account_id.acc_number)
			acc_numbers = [int(i) for i in record.line_ids.mapped('payment_acc_number')]
			acc_numbers.append(acc_number)
			check_number = str(sum(acc_numbers))
			f.write('1{lines}{date}{charge_type}{currency}{account}{total}{reference}{flag}{checksum}\r\n'.format(
					lines = self.parse_number_txt(len(record.line_ids), 'int', 6),
					date = process_date,
					charge_type = 'C',
					currency = '0001' if record.charge_currency_id.name == 'PEN' else '1001',
					account = record.charge_account_id.acc_number + aux_account[len(record.charge_account_id.acc_number):],
					total = self.parse_number_txt(record.total_charge, 'float', 17),
					reference = aux_ref[:-len(record.reference)] + record.reference if record.reference else aux_ref,
					flag = record.flag,
					checksum = aux_check[:-len(check_number)] + check_number
				))
			for line in record.line_ids:
				payment_aux = ' ' * 20
				p_doc_aux = ' ' * 12
				bene_aux = ' ' * 75
				bene_ref_aux = ' ' * 40
				company_aux = ' ' * 20
				doc_aux = '0' * 15
				f.write('2{account_type}{payment_doc}{payment_type}{p_doc_type}{p_doc_num}   {beneficiary_name}\
{beneficiary_ref}{company_ref}{currency}{amount}{flag}\r\n'.format(
					account_type = line.account_type,
					payment_doc = line.payment_acc_number + payment_aux[len(line.payment_acc_number):],
					payment_type = line.payment_type,
					p_doc_type = line.partner_doc_type,
					p_doc_num = line.partner_doc_number + p_doc_aux[len(line.partner_doc_number):],
					beneficiary_name = line.beneficiary_name + bene_aux[len(line.beneficiary_name):] if line.beneficiary_name else bene_aux,
					beneficiary_ref = line.beneficiary_ref + bene_ref_aux[len(line.beneficiary_ref):] if line.beneficiary_ref else bene_ref_aux,
					company_ref = line.company_ref + company_aux[len(line.company_ref):] if line.company_ref else company_aux,
					currency = '0001' if record.charge_currency_id.name == 'PEN' else '1001',
					amount = self.parse_number_txt(line.amount, 'float', 17),
					flag = line.flag,
					))
				f.write('3{doc_type}{doc_number}{amount}\r\n'.format(
					doc_type = line.doc_type,
					doc_number = doc_aux[:-len(line.doc_number)] + line.doc_number,
					amount = self.parse_number_txt(line.amount, 'float', 17),
					))
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BCP.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentBCPLine(models.Model):
	_name = 'multiple.payment.bcp.line'
	_description = 'Multiple Payment BCP Line'

	bcp_id = fields.Many2one('multiple.payment.bcp', ondelete='cascade')
	move_id = fields.Many2one('account.move', string='Factura', required=True)
	account_type = fields.Selection([
									('A', 'Cuenta de Ahorros'), 
									('C', 'Cuenta Corriente'), 
									('M', 'Cuenta Maestra'),
									('B', 'Interbancaria')], string='Tipo de Cuenta de Abono', required=True)
	payment_type = fields.Selection([
									('1', 'Efectivo'),
									('2', 'Cheque Gerencia')], string='Modalidad de Pago', required=True)
	partner_doc_type = fields.Selection([
								('1', 'DNI'),
								('3', 'CE'),
								('4', 'PAS'),
								('6', 'RUC'),
								('7', 'FIC')], string='Tipo de Documento del Proveedor', required=True)
	partner_doc_number = fields.Char(string='Numero de Documento del Proveedor', size=12, required=True)
	payment_acc_number = fields.Char(string='Numero de Cuenta de Abono', size=20, required=True)
	beneficiary_name = fields.Char(string='Nombre del Proveedor', size=70, required=True)
	beneficiary_ref = fields.Char(string='Referencia para el benficiario', size=40)
	company_ref = fields.Char(string='Referencia para la Empresa', size=20)
	amount = fields.Float(string='Importe a Abonar', digits=(13, 2), required=True)
	flag = fields.Selection([
							('N', 'No desea validar IDC vs Cuenta'),
							('S', 'Si desea validar IDC vs Cuenta')], default='N', string='Flag validar IDC')
	doc_type = fields.Selection([
								('F', 'Factura del proveedor'),
								('N', 'Nota credito proveedor'),
								('C', 'Nota debito proveedor'),
								('E', 'Factura de la empresa'),
								('M', 'Nota credito empresa'),
								('B', 'Nota debito empresa'),
								('Z', 'Cobranza'),
								('D', 'Otros')], default='F', string='Tipo de Documento a Pagar', required=True)
	doc_number = fields.Char(string='Numero de Documento a Pagar', size=15)