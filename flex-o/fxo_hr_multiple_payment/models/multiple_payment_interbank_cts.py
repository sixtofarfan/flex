# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentInterbankCTS(models.Model):
	_name = 'multiple.payment.interbank.cts'
	_description = 'Multiple Payment Interbank CTS'

	company_code = fields.Char(string='Codigo de la Empresa', size=4, required=True)
	service_code = fields.Char(string='Codigo del Servicio', size=2, required=True)
	charge_account_id = fields.Many2one('res.partner.bank', string='Cuenta de Cargo', required=True, states={'txt': [('readonly', True)]}, domain=[('type_of_account', 'in', ['0', '1'])])
	charge_currency_id = fields.Many2one(related='charge_account_id.currency_id', string='Moneda de Cuenta de Cargo')
	total_charge = fields.Float(compute='_get_total_charge', string='Importe a Cargar', required=True, digits=(13, 2))
	process_date = fields.Datetime(string='Fecha de Proceso', states={'txt': [('readonly', True)]})
	process_type = fields.Selection([('0', 'En Linea'), ('1', 'En diferido')], default='0', string='Tipo de Proceso', required=True)
	after_process_date = fields.Date(string='Fecha de Proceso Diferido', states={'txt': [('readonly', True)]})
	reference = fields.Char(string='Referencia', size=12, states={'txt': [('readonly', True)]})
	line_ids = fields.One2many('multiple.payment.interbank.cts.line', 'interbank_cts_id', states={'txt': [('readonly', True)]})
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
		if not MainParameter.interbank_bank:
			raise UserError('Falta configurar el un Banco Interbank en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
		for record in self:
			if record.charge_account_id.bank_id != MainParameter.interbank_bank:
				raise UserError('No se puede utilizar una cuenta bancaria diferente a Interbank')
			if record.charge_account_id.type_of_account not in ['0', '1']:
				raise UserError('La cuenta debe ser Corriente o de Ahorros')
			if len(record.charge_account_id.acc_number) != 13:
				raise UserError('La cuenta consta de 13 posiciones')

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

	def get_interbank_cts_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sInterbank CTS.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			aux = '00'
			if not self.env.user.partner_id.tz:
				raise UserError('Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
			if record.process_date:
				tz = pytz.timezone(self.env.user.partner_id.tz)
				date_tz = pytz.utc.localize(record.process_date).astimezone(tz)
				year, month, day = str(date_tz.year), str(date_tz.month), str(date_tz.day)
				hour, minute, second = str(date_tz.hour), str(date_tz.minute), str(date_tz.second)
				process_date = year + aux[:-len(month)] + month + aux[:-len(day)] + day + aux[:-len(hour)] + hour + aux[:-len(minute)] + minute + aux[:-len(second)] + second
			else:
				process_date = ' ' * 14
			if record.after_process_date:
				year, month, day = str(record.after_process_date.year), str(record.after_process_date.month), str(record.after_process_date.day)
				after_process_date = year + aux[:-len(month)] + month + aux[:-len(day)] + day
			else:
				after_process_date = ' ' * 8
			aux_ref = ' ' * 12
			aux_account = ' ' * 13
			aux_check = '0' * 15
			acc_number = int(record.charge_account_id.acc_number)
			acc_numbers = [int(i) for i in record.line_ids.mapped('payment_acc_number')]
			acc_numbers.append(acc_number)
			check_number = str(sum(acc_numbers))
			f.write('0106{company}{service}{account}{type_account}{currency}{reference}{date}{process_type}{after_date}{lines}{soles_total}{usd_total}MC001\r\n'.format(
					company = record.company_code if record.company_code else ' ' * 4,
					service = record.service_code if record.service_code else ' ' * 2,
					account = record.charge_account_id.acc_number + aux_account[len(record.charge_account_id.acc_number):],
					type_account = '001' if record.charge_account_id.type_of_account == '0' else '002',
					currency = '01' if record.charge_currency_id.name == 'PEN' else '10',
					reference = record.reference + aux_ref[len(record.reference):] if record.reference else aux_ref,
					date = process_date,
					process_type = record.process_type,
					after_date = after_process_date,
					lines = self.parse_number_txt(len(record.line_ids), 'int', 6),
					soles_total = self.parse_number_txt(record.total_charge, 'float', 15) if record.charge_currency_id.name == 'PEN' else '0' * 15,
					usd_total = self.parse_number_txt(record.total_charge, 'float', 15) if record.charge_currency_id.name == 'USD' else '0' * 15,
				))
			for line in record.line_ids:
				p_doc_aux = ' ' * 20
				p_doc_aux2 = ' ' * 15
				bene_aux = ' ' * 60
				doc_aux = ' ' * 20
				phone_aux = ' ' * 40
				email_aux = ' ' * 140
				acc_num_aux = ' ' * 20
				f.write('02{benef_code}{doc_type}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
{account_currency}{account_office}{acc_number}{person_type}{p_doc_type}{p_doc_num}{beneficiary_name}{currency_cts}{amount_cts}\
{filler}{cell_phone}{email}\r\n'.format(
					benef_code = line.partner_doc_number + p_doc_aux[len(line.partner_doc_number):],
					doc_type = line.doc_type if line.doc_type else ' ',
					doc_number = line.doc_number + doc_aux[:len(line.doc_number)] if line.doc_number else doc_aux,
					date_to = ' ' * 8,
					charge_currency = '01' if record.charge_currency_id.name == 'PEN' else '10',
					amount = self.parse_number_txt(line.amount, 'float', 15),
					charge_type = '09',
					account_type = '007',
					account_currency = '01' if record.charge_currency_id.name == 'PEN' else '10',
					account_office = line.payment_acc_number[:3],
					acc_number = line.payment_acc_number[3:] + acc_num_aux[len(line.payment_acc_number[3:]):],
					person_type = line.person_type if line.person_type else ' ',
					p_doc_type = line.partner_doc_type,
					p_doc_num = line.partner_doc_number + p_doc_aux2[len(line.partner_doc_number):],
					beneficiary_name = line.beneficiary_name + bene_aux[len(line.beneficiary_name):],
					currency_cts = '01' if record.charge_currency_id.name == 'PEN' else '10',
					amount_cts = self.parse_number_txt(line.amount_cts, 'float', 15),
					filler = ' ' * 6,
					cell_phone = line.cell_phone + phone_aux[len(line.cell_phone):] if line.cell_phone else phone_aux,
					email = line.email + email_aux[len(line.email):] if line.email else email_aux,
					))
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Interbank CTS.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentInterbankCTSLine(models.Model):
	_name = 'multiple.payment.interbank.cts.line'
	_description = 'Multiple Payment Interbank CTS Line'

	interbank_cts_id = fields.Many2one('multiple.payment.interbank.cts', ondelete='cascade')
	move_id = fields.Many2one('hr.cts.line', string='CTS', required=True)
	partner_doc_type = fields.Selection([
								('01', 'DNI'),
								('02', 'RUC'),
								('03', 'Carnet Extranjeria'),
								('05', 'Pasaporte')], string='Tipo de Documento del Proveedor', required=True)
	partner_doc_number = fields.Char(string='Numero de Documento del Proveedor', size=12, required=True)
	payment_acc_number = fields.Char(string='Numero de Cuenta de Abono', size=20, required=True)
	person_type = fields.Selection([('P', 'Persona Natural'), 
									('C', 'Comercial'), 
									('J', 'Juridica')], default='P', string='Tipo de Persona')
	beneficiary_name = fields.Char(string='Nombre del Proveedor', size=70, required=True)
	amount_cts = fields.Float(string='Monto Intangible CTS', digits=(13, 2), required=True)
	cell_phone = fields.Char(string='Numero de Celular')
	email = fields.Char(string='Email')
	amount = fields.Float(string='Importe a Abonar', digits=(13, 2), required=True)
	doc_type = fields.Selection([
								('F', 'Factura del proveedor'),
								('C', 'Nota credito proveedor'),
								('D', 'Nota debito proveedor')], default='F', string='Tipo de Documento a Pagar', required=True)
	doc_number = fields.Char(string='Numero de Documento a Pagar', size=15)