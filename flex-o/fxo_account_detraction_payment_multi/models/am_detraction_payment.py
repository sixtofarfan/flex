# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64

class AMDetractionPayment(models.Model):
	_name = 'am.detraction.payment'
	_description = 'Account Move Detraction Payment'

	journal_id = fields.Many2one('account.journal', string='Diario')
	payment_line_ids = fields.One2many('am.detraction.payment.line', 'am_detraction_id')
	state = fields.Selection([('draft', 'Borrador'),
							  ('txt', 'Txt Generado'),
							  ('payed', 'Pagado')], default='draft', string='Estado')

	def turn_txt(self):
		for record in self:
			record.state = 'txt'

	def turn_draft(self):
		for record in self:
			record.state = 'draft'

	def get_am_wizard(self):
		return {
			'name': 'Generacion de Txt para Pagos de Apuntes de Detraccion',
			'type': 'ir.actions.act_window',
			'res_model': 'am.detraction.payment.wizard',
			'views': [[False, 'form']],
			'context': self._context,
			'target': 'new',
		}

	def get_move_line_txt(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter or not MainParameter.dir_create_file:
			raise UserError(u'No existe un Directorio de Descarga configurado en Parametros Principales de Nomina para su Compañía')
		doc_name = '%sPagos_Detracciones.txt' % MainParameter.dir_create_file
		f = open(doc_name, 'w+')
		for record in self:
			for c, line in enumerate(record.payment_line_ids, 1):
				MoveLine = line.move_line_id
				f.write('{c}|{doc_type}|{doc_number}|{name}|00|{code_operation}|{amount}|{operation_type}|\
{period}|{move_type}|{move_serie}|{move_number}'.format(
						c = c,
						doc_type = line.doc_type,
						doc_number = line.doc_number,
						name = line.name,
						code_operation = line.code_operation,
						amount = line.amount,
						operation_type = line.operation_type,
						period = line.period,
						move_type = line.move_type,
						move_serie = line.move_serie,
						move_number = line.move_number,
					))
			record.turn_txt()
		f.close()
		f = open(doc_name, 'rb')
		return self.env['popup.it'].get_file('Pago Detracciones.txt', base64.encodestring(b''.join(f.readlines())))

class AMDetractionPaymentLine(models.Model):
	_name = 'am.detraction.payment.line'
	_description = 'Account Move Detraction Payment Line'

	am_detraction_id = fields.Many2one('am.detraction.payment', ondelete='cascade')
	move_line_id = fields.Many2one('account.move.line', string='Apunte Contable')
	doc_type = fields.Char(string='Tipo de Documento del Cliente')
	doc_number = fields.Char(string='Numbero de Documento del Cliente')
	name = fields.Char(string='Nombre del Cliente')
	code_operation = fields.Char(string='Bien o Servicio')
	amount = fields.Char(string='Monto')
	operation_type = fields.Char(string='Tipo de Operacion')
	period = fields.Char(string='Periodo')
	move_type = fields.Char(string='Tipo de Comprobante')
	move_serie = fields.Char(string='Serie de Comprobante')
	move_number = fields.Char(string='Numero de Comprobante')