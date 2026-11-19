# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import *
import base64, pytz
from dateutil.relativedelta import relativedelta

class MultiplePaymentBBVA(models.Model):
	_name = 'multiple.payment.bbva'
	_description = 'Multiple Payment BBVA'

	charge_account_id = fields.Many2one('res.partner.bank', string='Cuenta de Cargo', required=True, states={'txt': [('readonly', True)]})
	charge_currency_id = fields.Many2one(related='charge_account_id.currency_id', string='Moneda de Cuenta de Cargo')
	total_charge = fields.Float(compute='_get_total_charge', string='Importe a Cargar', required=True, digits=(13, 2))
	process_type = fields.Selection([
									('A', 'Inmediato'), 
									('H', 'Hora de proceso'),
									('F', 'Fecha futura')], default='A', string='Tipo de Proceso', required=True, states={'txt': [('readonly', True)]})
	process_date = fields.Date(string='Fecha de Proceso', states={'txt': [('readonly', True)]})
	process_hour = fields.Selection([
									('B', '11:00 a.m.'),
									('C', '03:00 p.m.'),
									('D', '07:00 p.m.')
									], default='B', string='Hora de Proceso', states={'txt': [('readonly', True)]})
	reference = fields.Char(string='Referencia', size=25, states={'txt': [('readonly', True)]})
	owner_validation = fields.Selection([
										('S', 'Valida, si hay error rechaza el abono'),
										('N', 'No valida')], default='S', string='Validacion de Pertenencia', required=True, states={'txt': [('readonly', True)]})
	line_ids = fields.One2many('multiple.payment.bbva.line', 'bbva_id', states={'txt': [('readonly', True)]})
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
		if not MainParameter.bbva_bank:
			raise UserError('Falta configurar el un Banco BBVA en Parametros Principales de Contabilidad en la pestaña Pagos a Bancos')
		for record in self:
			if record.charge_account_id.bank_id != MainParameter.bbva_bank:
				raise UserError('No se puede utilizar una cuenta bancaria diferente a BBVA')
			if len(record.charge_account_id.acc_number) != 20 or record.charge_account_id.acc_number[:4] != '0011':
				raise UserError("""
El numero de cuenta debe tener el siguiente formato:
Número de cuenta 0011xxxxDCnnnnnnnnnn
Donde:
xxxx = Oficina
DC, dígitos de control. Si no los conoce informar "00"
nnnnnnnnnn = Núm. de cuenta""")

	@api.constrains('process_date')
	def verify_date(self):
		today = fields.Date.today()
		#if not self.env.user.partner_id.tz:
		#	raise UserError('Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
		#tz = pytz.timezone(self.env.user.partner_id.tz)
		for record in self:
			if record.process_type == 'F':
				#date_tz = pytz.utc.localize(record.process_date).astimezone(tz)
				if record.process_date:
					if record.process_date <= today or record.process_date > today + relativedelta(months=6):
						raise UserError('La Fecha de Proceso ingresada debe ser mayor al dia de hoy y menor hasta 6 meses a futuro')

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

	def get_bbva_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sBBVA.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			if record.process_type == 'F':
				aux = '00'
				year, month, day = str(record.process_date.year), str(record.process_date.month), str(record.process_date.day)
				process_date = year + aux[:-len(month)] + month + aux[:-len(day)] + day
			aux_ref = ' ' * 25
			if len(record.charge_account_id.acc_number) != 20 or record.charge_account_id.acc_number[0:4] != '0011':
				raise UserError("""
El numero de cuenta debe tener el siguiente formato:
Número de cuenta 0011xxxxDCnnnnnnnnnn
Donde:
xxxx = Oficina
DC, dígitos de control. Si no los conoce informar "00"
nnnnnnnnnn = Núm. de cuenta""")
			f.write('750{account}{currency}{total}{process}{date}{hour}{reference}{lines}{valid}'.format(
					account = record.charge_account_id.acc_number,
					currency = record.charge_currency_id.name,
					total = self.parse_number_txt(record.total_charge, 'float', 15),
					process = record.process_type,
					date = process_date if record.process_type == 'F' else ' ' * 8,
					hour = record.process_hour if record.process_type == 'H' else ' ',
					reference = aux_ref[:-len(record.reference)] + record.reference if record.reference else aux_ref,
					lines = self.parse_number_txt(len(record.line_ids), 'int', 6),
					valid = record.owner_validation,
				) + ' ' * 15 + ' ' * 3 + ' ' * 30 + ' ' * 20 + '\r\n')
			for line in record.line_ids:
				p_doc_aux = ' ' * 12
				bene_aux = ' ' * 40
				doc_aux = ' ' * 12
				ref_aux = ' ' * 40
				alert_aux = ' ' * 50
				f.write('002{p_doc_type}{p_doc_num}{charge_type}{payment_doc}{beneficiary_name}{amount}{doc_type}\
{doc_number}{group_payment}{reference}{alert_indicator}{alert_value}'.format(
					p_doc_type = line.partner_doc_type,
					p_doc_num = line.partner_doc_number + p_doc_aux[len(line.partner_doc_number):],
					charge_type = line.charge_type,
					payment_doc = line.payment_acc_number,
					beneficiary_name = line.beneficiary_name + bene_aux[len(line.beneficiary_name):],
					amount = self.parse_number_txt(line.amount, 'float', 15),
					doc_type = line.doc_type,
					doc_number = line.doc_number + doc_aux[len(line.doc_number):],
					group_payment = line.group_payment,
					reference = line.reference + ref_aux[len(line.reference):] if line.reference else ref_aux,
					alert_indicator = line.alert_indicator if line.alert_indicator else ' ',
					alert_value = line.alert_value + alert_aux[len(line.alert_aux):] if line.alert_value else alert_aux,
					) + ' ' * 30 + ' ' * 2 + ' ' * 30 + ' ' * 18 + '\r\n')
		self.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('BBVA.txt', base64.encodestring(b''.join(f.readlines())))

class MultiplePaymentBBVALine(models.Model):
	_name = 'multiple.payment.bbva.line'
	_description = 'Multiple Payment BBVA Line'

	bbva_id = fields.Many2one('multiple.payment.bbva', ondelete='cascade')
	move_id = fields.Many2one('account.move', string='Factura', required=True)
	partner_doc_type = fields.Selection([
								('L', 'DNI o LE'),
								('R', 'RUC'),
								('M', 'Carne Militar'),
								('E', 'Carne Extranjeria'),
								('P', 'Pasaporte')], string='Tipo de Documento del Partner', required=True)
	charge_type = fields.Selection([
								('P', 'Propio Banco'),
								('I', 'Interbancario'),
								('O', 'Ordenes de Pago o Cheques de Gerencia')], string='Tipo de Abono', required=True)
	partner_doc_number = fields.Char(string='Numero de Documento del Partner', size=12, required=True)
	payment_acc_number = fields.Char(string='Numero de Cuenta de Abono', size=20, required=True)
	beneficiary_name = fields.Char(string='Nombre del Beneficiario', size=40, required=True)
	amount = fields.Float(string='Importe a Abonar', digits=(13, 2), required=True)
	doc_type = fields.Selection([
								('F', 'Factura'),
								('B', 'Boleta'),
								('N', 'Nota de Credito')], string='Tipo de Documento')
	doc_number = fields.Char(string='Numero de Documento', size=12)
	group_payment = fields.Selection([
									('S', 'Abono Agrupado'),
									('N', 'Abono Individual')], string='Abono Agrupado')
	reference = fields.Char(string='Referenca', size=40)
	alert_indicator = fields.Selection([
									('E', 'E-mail'),
									('C', 'Celular')], default='E', string='Indicador de Aviso')
	alert_value = fields.Char(string='Medio de Aviso', size=50)