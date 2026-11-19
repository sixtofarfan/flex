# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class HrCtsLine(models.Model):
	_inherit = 'hr.cts.line'

	exchange_type = fields.Float(default=1)

	def get_computed_line(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		Liquidation = self.liquidation_id
		context = self._context.copy()
		context.update({
			'sixth_of_gratification': self.sixth_of_gratification,
			'commission': self.commission,
			'extra_hours': self.extra_hours,
			'employee_id': self.employee_id,
		})
		MainParameter.with_context(context).compute_benefits(Liquidation, Liquidation.cts_type, liquidation=Liquidation)
		self.unlink()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.liquidation",
			"res_id": Liquidation.id,
			"views": [[False, "form"]],
			"name": "Liquidacion %s" % Liquidation.payslip_run_id.name,
		}