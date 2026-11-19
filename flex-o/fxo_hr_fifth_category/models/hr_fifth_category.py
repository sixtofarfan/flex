# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
import base64

class HrFifthCategoryLine(models.Model):
	_inherit = 'hr.fifth.category.line'

	custom_ext_rem = fields.Float(string='Remuneracion Extraordinaria Anterior')
	custom_past_rem = fields.Float(string='Remuneraciones Anteriores Regularizado')

	def compute_fifth_line(self):
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		MainParameter.check_fifth_values()
		ReportBase = self.env['report.base']
		#This line was added because the user used to discard a line after the computation so this create 
		#a line whithout header and that cause compute errors
		self.env['hr.fifth.category.line'].search([('fifth_category_id', '=', None), ('id', 'not in', self.ids)]).unlink()

		for record in self:
			Slip = record.slip_id
			month = Slip.date_from.month
			proy_month = self.get_month_equivalence_proy(month)
			rent_month = self.get_month_equivalence_rent(month)
			FiscalYear = self.env['account.fiscal.year'].search([('date_from', '<=', Slip.date_from), ('date_to', '>=', Slip.date_from)])
			uit = FiscalYear.uit
			Employee, Contract = Slip.employee_id, Slip.contract_id
			if month >= 7:
				grat_july = self.env['hr.gratification.line'].search([
																('gratification_id.type', '=', '07'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])
			if month == 12:
				grat_december = self.env['hr.fifth.category.line'].search([
																('gratification_id.type', '=', '12'), 
																('employee_id', '=', Employee.id),
																('gratification_id.fiscal_year_id', '=', FiscalYear.id)
															])

			date_ini_reg=str(Slip.date_from.year)+'-01-01'
			date_end_reg=str(Slip.date_to.year)+'-12-31'

			reg_ant = self.env['hr.fifth.category.line'].search([
																('slip_id.date_from', '>=', date_ini_reg), 
																('slip_id.date_to', '<=', date_end_reg), 
																('slip_id.employee_id', '=', Employee.id),
																('custom_past_rem','>',0)
															])
			amoun_ant=0
			record.custom_past_rem=0
			if len(reg_ant)>0:
				amoun_ant=reg_ant[0].custom_past_rem
				record.custom_past_rem=amoun_ant

			dateto = Slip.date_from- timedelta(days=1)
			monto=0
			if Slip.date_from.year == 2021:
				cadsql = """select sum(hr_payslip_line.total) as amount from hr_payslip
				inner join hr_payslip_line on hr_payslip.id = hr_payslip_line.slip_id
				where hr_payslip.employee_id = %s
				and hr_payslip.date_from>='%s' and hr_payslip.date_to<='%s'
				and hr_payslip_line.code in ('ROAQ','REAQ') """%(str(Slip.employee_id.id),'2021-01-01',dateto)
				self.env.cr.execute(cadsql)
				datasql = self.env.cr.dictfetchall()
				monto=datasql[0]['amount']
			else:
				monto = self.get_past_rem(Slip, FiscalYear.date_from)

			record.monthly_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_afect_sr_id).total
			record.contrac_proy_rem = Contract.fifth_rem_proyected
			record.proy_rem = record.contrac_proy_rem * proy_month + record.monthly_rem
			record.grat_july = grat_july.total_grat if month >= 7 and grat_july else Contract.grat_july_proyected
			record.grat_december = grat_december.total_grat if month == 12 and grat_december else Contract.grat_december_proyected
			# print(self.get_past_rem(Slip, FiscalYear.date_from), record.custom_past_rem)
			record.past_rem = monto
			#record.past_rem = self.get_past_rem(Slip, FiscalYear.date_from) + record.custom_past_rem if record.custom_past_rem==0 else record.custom_past_rem
			record.total_proy = record.proy_rem + record.grat_july + record.grat_december + record.other_emp_proy_rem + record.past_rem
			record.seven_uit = 7 * uit
			record.net_rent = record.total_proy - record.seven_uit
			tax_proy = self.get_tax_proy(record.net_rent, MainParameter.rate_limit_ids)
			record.tax_proy = 0 if tax_proy < 0 else tax_proy
			record.past_months_ret = self.get_past_months_ret(Slip, FiscalYear.date_from)
			record.annual_ret = record.tax_proy - record.past_months_ret - record.other_emp_ret
			record.monthly_rent = ReportBase.custom_round(record.annual_ret/rent_month, 2)
			record.ext_rem = Slip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.fifth_extr_sr_id).total + record.custom_ext_rem
			record.total_net_rent = record.ext_rem + record.net_rent
			ext_ret = self.get_tax_proy(record.total_net_rent, MainParameter.rate_limit_ids) - record.tax_proy
			record.ext_ret = 0 if ext_ret < 0 else ext_ret
			record.monthly_ret = record.monthly_rent + record.ext_ret
			# print(record.monthly_ret,self._context.get('line_form', False))
			if not record.monthly_ret > 0 and not self._context.get('line_form', False):
				record.unlink()

