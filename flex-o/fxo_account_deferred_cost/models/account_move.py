# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
	_inherit = 'account.move'

	is_difered_cost = fields.Boolean(string='Es Gasto Diferido', default=False)
	difering_cost = fields.Boolean(string='Diferir Costo', default=False)
	difered_move_id = fields.Many2one('account.move', string='Asiento Diferido', copy=False)
	difered_move_tax_id = fields.Many2one('account.move', string='Asiento de Impuesto Diferido', copy=False)
	return_move_id = fields.Many2one('account.move', string='Asiento de Extorno', copy=False)
	provision_move_id = fields.Many2one('account.move', string='Asiento de Provision', copy=False)

	def set_difered_cost_account(self):
		Lines = self.invoice_line_ids.filtered(lambda l: l.account_id.code.startswith('63') or l.account_id.code.startswith('65'))
		if any(not l.difered_account_id for l in Lines):
			raise UserError('Todas las lineas con cuenta 63 o 65 deben tener una cuenta diferida asociada para completar el proceso')
		for line in Lines:
			acc = line.account_id.id
			dif = line.difered_account_id.id
			line.write({'account_id': dif, 'difered_account_id': acc})
		self.is_difered_cost = True

	def button_draft(self):
		if self.difered_move_id or self.difered_move_tax_id or self.return_move_id or self.provision_move_id:
			raise UserError('No se puede cambiar a borrador un Comprobante con asientos relacionados')
		return super(AccountMove, self).button_draft()

	def get_difered_wizard_tax_confirmation(self):
		for record in self:
			if record.type not in ['in_invoice', 'in_refund']:
				raise UserError('Esta funcionalidad solo esta habilitada para Facturas de Proveedor')
		return {
			'name': 'Confirmacion',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.difered.wizard',
			'views': [(self.env.ref('fxo_account_deferred_cost.view_account_move_difered_wizard_form_tax_confirmation').id, 'form')],
			'context': self._context,
			'target': 'new',
		}

	def get_difered_wizard_tax(self):
		for record in self:
			if record.type not in ['in_invoice', 'in_refund']:
				raise UserError('Esta funcionalidad solo esta habilitada para Facturas de Proveedor')
			if not record.date_detraccion:
				raise UserError('La factura %s no tiene fecha de Detraccion' % record.name)
			context = self._context.copy()
			context.update({'default_date': record.date_detraccion})
		return {
			'name': 'Generar Asiento de Impuesto',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.difered.wizard',
			'views': [(self.env.ref('fxo_account_deferred_cost.view_account_move_difered_wizard_form_tax').id, 'form')],
			'context': context,
			'target': 'new',
		}

	def get_difered_wizard_derive(self):
		return {
			'name': 'Generar Asientos de Extorno y Provision',
			'type': 'ir.actions.act_window',
			'res_model': 'account.move.difered.wizard',
			'views': [(self.env.ref('fxo_account_deferred_cost.view_account_move_difered_wizard_form_derive').id, 'form')],
			'context': self._context,
			'target': 'new',
		}

class AccountMoveLine(models.Model):
	_inherit = 'account.move.line'

	move_is_difered_cost = fields.Boolean(related='move_id.is_difered_cost', store=True)
	difered_account_id = fields.Many2one('account.account', string='Cuenta Diferida', default=lambda self: self._get_difered_account())
	storable_account_tax = fields.Many2one('account.account', string='Cuenta Anterior Almacenada')

	@api.model
	def _get_difered_account(self):
		MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
		if not MainParameter.difered_cost_account:
			return None
		else:
			return MainParameter.difered_cost_account.id