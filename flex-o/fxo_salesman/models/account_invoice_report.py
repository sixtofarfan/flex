# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoiceReport(models.Model):
	_inherit = 'account.invoice.report'

	salesman_id = fields.Many2one('res.partner', string='Codigo Vendedor')

	@api.model
	def _select(self):
		return '''
			SELECT
				line.id,
				line.move_id,
				line.product_id,
				line.account_id,
				line.analytic_account_id,
				line.journal_id,
				line.company_id,
				line.currency_id,
				line.partner_id AS commercial_partner_id,
				move.name,
				rps.id As salesman_id,
				move.state,
				move.type,
				move.partner_id,
				move.invoice_user_id,
				move.fiscal_position_id,
				move.invoice_payment_state,
				move.invoice_date,
				move.invoice_date_due,
				move.invoice_payment_term_id,
				move.invoice_partner_bank_id,
				move.amount_residual_signed                                 AS residual,
				move.amount_total_signed                                    AS amount_total,
				uom_template.id                                             AS product_uom_id,
				template.categ_id                                           AS product_categ_id,
				SUM(line.quantity / NULLIF(COALESCE(uom_line.factor, 1) * COALESCE(uom_template.factor, 1), 0.0))
																			AS quantity,
				-SUM(line.balance)                                          AS price_subtotal,
				-SUM(line.balance / NULLIF(COALESCE(uom_line.factor, 1) * COALESCE(uom_template.factor, 1), 0.0))
																			AS price_average,
				COALESCE(partner.country_id, commercial_partner.country_id) AS country_id,
				1                                                           AS nbr_lines
		'''

	@api.model
	def _from(self):
		return '''
			FROM account_move_line line
				LEFT JOIN res_partner partner ON partner.id = line.partner_id
				LEFT JOIN product_product product ON product.id = line.product_id
				LEFT JOIN account_account account ON account.id = line.account_id
				LEFT JOIN account_account_type user_type ON user_type.id = account.user_type_id
				LEFT JOIN product_template template ON template.id = product.product_tmpl_id
				LEFT JOIN uom_uom uom_line ON uom_line.id = line.product_uom_id
				LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
				INNER JOIN account_move move ON move.id = line.move_id
				LEFT JOIN res_partner commercial_partner ON commercial_partner.id = move.commercial_partner_id
				LEFT JOIN res_partner rps ON rps.id = move.salesman_id 
		'''

	@api.model
	def _group_by(self):
		return '''
			GROUP BY
				line.id,
				line.move_id,
				line.product_id,
				line.account_id,
				line.analytic_account_id,
				line.journal_id,
				line.company_id,
				line.currency_id,
				line.partner_id,
				move.name,
				rps.id,
				move.state,
				move.type,
				move.amount_residual_signed,
				move.amount_total_signed,
				move.partner_id,
				move.invoice_user_id,
				move.fiscal_position_id,
				move.invoice_payment_state,
				move.invoice_date,
				move.invoice_date_due,
				move.invoice_payment_term_id,
				move.invoice_partner_bank_id,
				uom_template.id,
				template.categ_id,
				COALESCE(partner.country_id, commercial_partner.country_id)
		'''