# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from dateutil.relativedelta import relativedelta
import base64

class HrLiquidation(models.Model):
	_inherit = 'hr.liquidation'

	cts_count = fields.Integer(compute='_compute_cts_count')
	liq_ext_concept_ids = fields.One2many('hr.liquidation.extra_concepts', 'liquidation_id')

	def get_cts_employees(self):
		self.ensure_one()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.cts.line",
			"views": [[False, "tree"]],
			"domain": [['id', 'in', self.cts_line_ids.ids]],
			"name": "CTS",
		}

	def _compute_cts_count(self):
		for record in self:
			record.cts_count = len(self.cts_line_ids)

	def get_vacation_lines(self):
		year = int(self.fiscal_year_id.name)
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		MonthLot = self.payslip_run_id
		Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
															slip.contract_id.situation_id.code == '0' and
															not slip.contract_id.less_than_four).mapped('employee_id')
		if self._context.get('employee_id'):
			Employees = self._context.get('employee_id')
		for Employee in Employees:
			bonus_months = months = days = lacks = 0
			Commissions = Bonus = ExtraHours = self.env['hr.payslip.line']
			MonthSlip = MonthLot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
			FirstContract = self.env['hr.contract'].get_first_contract(Employee, MonthSlip.contract_id)
			admission_date = Employee.emp_date_start if Employee.emp_date_start else FirstContract.date_start
			compute_date = date(admission_date.year, admission_date.month, admission_date.day)
			wage = FirstContract.wage
			household_allowance = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.household_allowance_sr_id).total
			compute_payslip_date = date(compute_date.year, compute_date.month, 1)
			Lots = self.env['hr.payslip.run'].search([('date_start', '>=', compute_payslip_date),
													  ('date_end', '<=', MonthSlip.date_to)])
			for Lot in Lots:
				EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
				SalaryRules = EmployeeSlips.mapped('line_ids')
				WorkedDays = EmployeeSlips.mapped('worked_days_line_ids')
				WorkingWD =	sum(WorkedDays.filtered(lambda line: line.wd_type_id in MainParameter.working_wd_ids).mapped('number_of_days'))
				if WorkingWD >= 30:
					months += 1
				else:
					days += WorkingWD
				LackWD = sum(WorkedDays.filtered(lambda line: line.wd_type_id == MainParameter.lack_wd_id).mapped('number_of_days'))
				lacks += LackWD

			date_limit_to = MonthSlip.contract_id.date_end
			date_limit_from = self.get_date_limit_from(date_limit_to)
			Lots = self.env['hr.payslip.run'].search([('date_start', '>=', date_limit_from),
													  ('date_end', '<=', date_limit_to)])
			bonus_months = len(Lots.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee))
			for Lot in Lots:
				EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee)
				SalaryRules = EmployeeSlips.mapped('line_ids')
				Commissions += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.commission_sr_ids and line.total > 0)
				Bonus += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.bonus_sr_ids and line.total > 0)
				ExtraHours += SalaryRules.filtered(lambda line: line.salary_rule_id == MainParameter.extra_hours_sr_id and line.total > 0)
			if self._context.get('change_ctx'):
				commission = self._context.get('commission')
			else:
				commission = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Commissions)
			if self._context.get('change_ctx'):
				bonus = self._context.get('bonus')
			else:
				bonus = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, Bonus)
			if self._context.get('change_ctx'):
				extra_hours = self._context.get('extra_hours')
			else:
				extra_hours = MainParameter.calculate_bonus(admission_date, date_limit_from, bonus_months, ExtraHours)
			computable_remuneration = wage + household_allowance + commission + bonus + extra_hours
			medical_days, excess_medical_rest = MainParameter.calculate_excess_medical_rest(year, Employee)
			days = days + medical_days
			if days >= 30:
				days, months = MainParameter.get_months_of_30_days(days, months)
			if self._context.get('change_ctx'):
				days = self._context.get('days')
			if self._context.get('change_ctx'):
				months = self._context.get('months')
			if self._context.get('change_ctx'):
				lacks = self._context.get('lacks')
			amount_per_month = computable_remuneration/12 if MonthSlip.contract_id.labor_regime == 'general' else computable_remuneration/24
			amount_per_day = amount_per_month/30
			amount_per_lack = amount_per_day * lacks
			vacation_per_month = ReportBase.custom_round(amount_per_month * months, 2)
			vacation_per_day = ReportBase.custom_round(amount_per_day * days, 2)
			truncated_vacation = ReportBase.custom_round((vacation_per_month + vacation_per_day) - amount_per_lack, 2)
			accrued_vacation = advanced_vacation = 0
			if self._context.get('change_ctx'):
				accrued_vacation = self._context.get('accrued_vacation')
			if self._context.get('change_ctx'):
				advanced_vacation = self._context.get('advanced_vacation')
			total_vacation = truncated_vacation - advanced_vacation + accrued_vacation
			membership = MonthSlip.contract_id.membership_id
			onp = afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
			if membership.is_afp:
				afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
				afp_si = ReportBase.custom_round(membership.prima_insurance/100 * total_vacation, 2)
				afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * total_vacation, 2)
				afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * total_vacation, 2)
			else:
				onp = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
			total = ReportBase.custom_round(total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)
			vals = {
					'liquidation_id': self.id,
					'employee_id': Employee.id,
					'contract_id': MonthSlip.contract_id.id,
					'admission_date': admission_date,
					'compute_date': compute_date,
					'cessation_date': MonthSlip.contract_id.date_end,
					'membership_id': membership.id,
					'months': months,
					'days': days,
					'lacks': lacks,
					'wage': wage,
					'household_allowance': household_allowance,
					'commission': commission,
					'bonus': bonus,
					'extra_hours': extra_hours,
					'computable_remuneration': computable_remuneration,
					'amount_per_month': amount_per_month,
					'amount_per_day': amount_per_day,
					'vacation_per_month': vacation_per_month,
					'vacation_per_day': vacation_per_day,
					'truncated_vacation': truncated_vacation,
					'total_vacation': total_vacation,
					'accrued_vacation': accrued_vacation,
					'advanced_vacation': advanced_vacation,
					'onp': onp,
					'afp_jub': afp_jub,
					'afp_si': afp_si,
					'afp_mixed_com': afp_mixed_com,
					'afp_fixed_com': afp_fixed_com,
					'total': total
				}
			self.env['hr.liquidation.vacation.line'].create(vals)
	
	def get_liquidation(self):
		res = super(HrLiquidation, self).get_liquidation()
		self.liq_ext_concept_ids.unlink()
		for emp in self.employee_ids:
			self.env['hr.liquidation.extra_concepts'].create({
				'liquidation_id': self.id,
				'employee_id': emp.id,
			})
		return res

	def get_compensation_lines(self):
		MonthLot = self.payslip_run_id
		Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
															slip.contract_id.situation_id.code == '0').mapped('employee_id')
		self.employee_ids = [(6, 0, Employees.ids)]
		Employees = MonthLot.slip_ids.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
															slip.contract_id.situation_id.code == '0' and
															not slip.contract_id.less_than_four).mapped('employee_id')
		for Employee in Employees:
			Contract = MonthLot.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee).contract_id
			admission_date = Employee.emp_date_start if Employee.emp_date_start else self.env['hr.contract'].get_first_contract(Employee, Contract).date_start
			vals = {'liquidation_id': self.id,
					'employee_id': Employee.id,
					'contract_id': Contract.id,
					'admission_date': admission_date,
					'cessation_date': Contract.date_end}
			self.env['hr.compensation.line'].create(vals)

class HrLiquidationVacationLine(models.Model):
	_inherit = 'hr.liquidation.vacation.line'

	is_worked_day = fields.Boolean(string='Calculo de Dias Trabajados', default=True)
	basic_worked_day = fields.Float(string='Basico Dias Trabajados')

	@api.model
	def create(self, vals):
		res = super(HrLiquidationVacationLine, self).create(vals)
		res._get_total_vacation()
		return res

	@api.onchange('accrued_vacation', 'advanced_vacation', 'is_worked_day')
	def _get_total_vacation(self):
		ReportBase = self.env['report.base']
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		for record in self:
			Lot = record.liquidation_id.payslip_run_id
			afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
			MonthSlip = Lot.slip_ids.filtered(lambda l: l.employee_id == record.employee_id)
			record.total_vacation = record.accrued_vacation + record.truncated_vacation - record.advanced_vacation
			total_vacation = record.total_vacation
			if not MainParameter.liquidation_wd_rules_ids:
				raise UserError('No se han configurado Reglas para calculo de dias laboradso en liquidacion')
			WD_rules = MonthSlip.line_ids.filtered(lambda l: l.salary_rule_id.id in MainParameter.liquidation_wd_rules_ids.ids)
			if record.is_worked_day:
				record.basic_worked_day = sum(WD_rules.mapped('total'))
				total_vacation += sum(WD_rules.mapped('total'))
			membership = record.contract_id.membership_id
			onp = afp_jub = afp_si = afp_mixed_com = afp_fixed_com = 0
			if membership.is_afp:
				afp_jub = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
				afp_si = ReportBase.custom_round(membership.prima_insurance/100 * total_vacation, 2)
				afp_mixed_com = ReportBase.custom_round(membership.mixed_commision/100 * total_vacation, 2)
				afp_fixed_com = ReportBase.custom_round(membership.fixed_commision /100 * total_vacation, 2)
			else:
				onp = ReportBase.custom_round(membership.retirement_fund/100 * total_vacation, 2)
			record.afp_jub = afp_jub
			record.afp_si = afp_si
			record.afp_mixed_com = afp_mixed_com
			record.afp_fixed_com = afp_fixed_com
			record.onp = onp
			record.total = ReportBase.custom_round(record.total_vacation - afp_jub - afp_si - afp_mixed_com - afp_fixed_com - onp, 2)


	def get_computed_line(self):
		Liquidation = self.liquidation_id
		context = self._context.copy()
		context.update({
			'change_ctx': True,
			'commission': self.commission,
			'bonus': self.bonus,
			'extra_hours': self.extra_hours,
			'employee_id': self.employee_id,
			'days': self.days,
			'months': self.months,
			'lacks': self.lacks,
			'accrued_vacation': self.accrued_vacation,
			'advanced_vacation': self.advanced_vacation,
		})
		Liquidation.with_context(context).get_vacation_lines()
		self.unlink()
		return {
			"type": "ir.actions.act_window",
			"res_model": "hr.liquidation",
			"res_id": Liquidation.id,
			"views": [[False, "form"]],
			"name": "Liquidacion %s" % Liquidation.payslip_run_id.name,
		}

class HrLiquidationExtraConcepts(models.Model):
	_name = 'hr.liquidation.extra_concepts'
	_description = 'Hr Liquidation Extra Concepts'

	liquidation_id = fields.Many2one('hr.liquidation', ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', string='Empleado')
	concept_ids = fields.One2many('hr.extra.concept', 'extra_concept_id', string='Conceptos Extras')
	income = fields.Float(string='Ingresos', compute='get_income_discount')
	expenses = fields.Float(string='Descuentos', compute='get_income_discount')

	@api.depends('concept_ids')
	def get_income_discount(self):
		for rec in self:
			In_Concepts = rec.concept_ids.filtered(lambda l: l.type == 'in')
			Out_Concepts = rec.concept_ids.filtered(lambda l: l.type == 'out')
			rec.income = sum(In_Concepts.mapped('amount')) if In_Concepts else 0
			rec.expenses = sum(Out_Concepts.mapped('amount')) if Out_Concepts else 0
	
	def get_concepts_view(self):
		return {
			"name": "Conceptos",
			"type": "ir.actions.act_window",
			"res_model": "hr.extra.concept",
			"views": [[False, "tree"]],
			"domain": [['extra_concept_id', '=', self.id]],
			"context": {
				'search_default_group_type': 1,
				'extra_id': self.id,
			},
			"target": "new",
		}

class HrExtraConcept(models.Model):
	_name = 'hr.extra.concept'
	_description = 'Hr Extra Concept'

	extra_concept_id = fields.Many2one('hr.liquidation.extra_concepts', ondelete='cascade')
	name = fields.Char(string='Descripcion')
	amount = fields.Float(string='Monto')
	type = fields.Selection([
		('in', 'Ingreso'),
		('out', 'Descuento'),
	], string='Tipo', default='in')

	@api.model
	def create(self,vals):
		rec = super(HrExtraConcept, self).create(vals)
		if not rec.extra_concept_id and self._context.get('extra_id'):
			rec.extra_concept_id = self._context.get('extra_id')
		return rec