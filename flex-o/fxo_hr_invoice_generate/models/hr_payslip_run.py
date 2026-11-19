# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'

	voucher_ids = fields.Many2many('account.move', 'payslip_run_voucher_rel', string='Boletas')
	voucher_count = fields.Integer(compute='_compute_voucher_count')

	def generate_voucher_moves(self):
		for i in self.voucher_ids: 
			if i.state != 'draft':
				i.button_draft()
			i.unlink()
		log, move_ids = '', []
		for slip in self.slip_ids:
			salary_rule_ids = slip.contract_id.salary_rule_ids
			if salary_rule_ids:
				PayslipLines = slip.line_ids.filtered(lambda s: s.salary_rule_id in salary_rule_ids)
				Contract = slip.contract_id
				Partner = slip.employee_id.user_id.partner_id
				Product = slip.contract_id.product_id
				if Partner and Product:
					Move = self.env['account.move'].create({
						'partner_id': Partner.id,
						'type_document_id': Contract.type_document_id.id if Contract.type_document_id else None,
						'serie_id': Contract.serie_id.id if Contract.serie_id else None,
						'invoice_date': fields.Date.today(),
						'journal_id': Contract.journal_id.id if Contract.journal_id else None,
						'date': fields.Date.today(),
						'type': 'out_invoice',
						'invoice_line_ids': [
							(0, 0, {
								'product_id': Contract.product_id.id if Contract.product_id else None,
								'account_id': Product.property_account_income_id.id if Product.property_account_income_id else None,
								'partner_id': Partner.id,
								'quantity': 1,
								'price_unit': pl.total,
								'tax_ids': [(6, 0, Product.taxes_id.ids)] if Product.taxes_id else None,
							}) for pl in PayslipLines
						]
					})
					move_ids.append(Move.id)
				else:
					log += 'El empleado %s no tiene usuario OperERP asociado o a su vez este usuario no tiene partner asociado\n' % slip.employee_id.name
		if move_ids:
			self.voucher_ids = [(6, 0, move_ids)]
		if log:
			return self.env['popup.it'].get_message('Ocurrieron los siguientes problemas:\n%s' % log)
		else:
			return self.env['popup.it'].get_message('Se crearon todas los comprobantes correctamente')

	def _compute_voucher_count(self):
		for rec in self:
			rec.voucher_count = len(rec.voucher_ids)

	def get_vouchers_view(self):
		return {
			"type": "ir.actions.act_window",
			"res_model": "account.move",
			"views": [
				(False, "tree"), 
				(False, "form"),
			],
			"domain": [['id', 'in', self.voucher_ids.ids]],
			"name": "Boletas",
		}