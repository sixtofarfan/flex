# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import *
from calendar import *
from collections import Counter

class HrMainParameter(models.Model):
	_inherit = 'hr.main.parameter'

	cts_release_template_id = fields.Many2one('hr.contract.template', string='Plantilla de Carta de Liberacion de CTS')
	work_voucher_template_id = fields.Many2one('hr.contract.template', string='Plantilla de Certificado de Trabajo')
	liquidation_wd_rules_ids = fields.Many2many('hr.salary.rule', 'liquidation_wd_rules_parameter', string='Reglas para calculo de Dias Laborados')

	def get_months_days_difference(self, date_from, date_to):
		if date_from.year == date_to.year and date_from.month == date_to.month:
			#### I don´t know if this is an error, posible fix
			return 0, date_to.day - date_from.day
		else:
			df_worked_days = 0
			months = (date_to.year - date_from.year) * 12 + (date_to.month - date_from.month - 1)
			df_last_day = monthrange(date_from.year, date_from.month)[1]
			if date_from.day == 1:
				months += 1
			else:
				df_worked_days += df_last_day - date_from.day + 1
			df_last_day = monthrange(date_to.year, date_to.month)[1]
			if date_to.day == df_last_day:
				months += 1
			else:
				df_worked_days += date_to.day
			if df_worked_days >= 30:
				return self.get_months_of_30_days(df_worked_days, months)
			else:
				return df_worked_days, months

	def compute_benefits(self, record, record_type, liquidation=False):
		year = int(record.fiscal_year_id.name)
		MainParameter = self.env['hr.main.parameter'].get_main_parameter()
		ReportBase = self.env['report.base']
		MainParameter.check_gratification_values() if record_type in ['07', '12'] else MainParameter.check_cts_values()
		if liquidation:
			MainParameter.check_liquidation_values()
			payslip_month = record.payslip_run_id.date_start.month
		if record_type == '07':
			date_from = datetime.strptime('01/01/%d' % year, '%d/%m/%Y').date()
			date_to = datetime.strptime('01/06/%d' % year, '%d/%m/%Y').date()
			month_date_from = datetime.strptime('01/06/%d' % year, '%d/%m/%Y').date()
			month_date_to = datetime.strptime('30/06/%d' % year, '%d/%m/%Y').date()
		if record_type == '12':
			date_from = datetime.strptime('01/07/%d' % year, '%d/%m/%Y').date()
			date_to = datetime.strptime('01/12/%d' % year, '%d/%m/%Y').date()
			month_date_from = datetime.strptime('01/12/%d' % year, '%d/%m/%Y').date()
			month_date_to = datetime.strptime('31/12/%d' % year, '%d/%m/%Y').date()
		if record_type == '11':
			date_from = datetime.strptime('01/05/%d' % year, '%d/%m/%Y').date()
			date_to = datetime.strptime('01/10/%d' % year, '%d/%m/%Y').date()
			month_date_from = datetime.strptime('01/10/%d' % year, '%d/%m/%Y').date()
			month_date_to = datetime.strptime('31/10/%d' % year, '%d/%m/%Y').date()
			required_gratification = {'year': str(year), 'month': '07'}
		if record_type == '05':
			if liquidation and payslip_month in [11, 12]:
				date_from = datetime.strptime('01/11/%d' % year, '%d/%m/%Y').date()
				date_to = datetime.strptime('01/04/%d' % (year + 1), '%d/%m/%Y').date()
			else:
				date_from = datetime.strptime('01/11/%d' % (year - 1), '%d/%m/%Y').date()
				date_to = datetime.strptime('01/04/%d' % year, '%d/%m/%Y').date()
			month_date_from = datetime.strptime('01/04/%s' % year, '%d/%m/%Y').date()
			month_date_to = datetime.strptime('30/04/%s' % year, '%d/%m/%Y').date()
			required_gratification = {'year': str(year - 1), 'month': '12'}

		if liquidation:
			MonthLot = record.payslip_run_id
			if record_type in ['05', '11']:
				FilteredSlips = MonthLot.slip_ids.filtered(lambda slip: not slip.contract_id.less_than_four)
			else:
				FilteredSlips = MonthLot.slip_ids
			Employees = FilteredSlips.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
																slip.contract_id.situation_id.code == '0' and
																slip.date_from <= slip.contract_id.date_end and
																slip.date_to >= slip.contract_id.date_end).mapped('employee_id')
		else:
			MonthLot = self.env['hr.payslip.run'].search([('date_start', '>=', month_date_from), ('date_end', '<=', month_date_to)])
			if record_type in ['05', '11']:
				FilteredSlips = MonthLot.slip_ids.filtered(lambda slip: not slip.contract_id.less_than_four)
			else:
				FilteredSlips = MonthLot.slip_ids
			Employees = FilteredSlips.filtered(lambda slip: slip.contract_id.labor_regime in ['general', 'small'] and
																slip.contract_id.situation_id.code != '0').mapped('employee_id')
		Lots = self.env['hr.payslip.run'].search([('date_start', '>=', date_from),
												  ('date_start', '<=', date_to)])
		if self._context.get('employee_id'):
			Employees = self._context.get('employee_id')
		for Employee in Employees:
			months = days = lacks = 0
			Commissions = Bonus = ExtraHours = self.env['hr.payslip.line']
			MonthSlip = FilteredSlips.filtered(lambda slip: slip.employee_id == Employee)
			FirstContract = self.env['hr.contract'].get_first_contract(Employee, MonthSlip.contract_id)
			admission_date = Employee.emp_date_start if Employee.emp_date_start else FirstContract.date_start
			if record_type in ['05', '11']:
				if record_type == '11':
					last_date = {'last_year': str(year), 'last_type': '05'}
				if record_type == '05':
					if liquidation and payslip_month in [11, 12]:
						last_date = {'last_year': str(year), 'last_type': '11'}
					else:
						last_date = {'last_year': str(year - 1), 'last_type': '11'}
				remaining_wage = self.env['hr.cts.line'].search([('employee_id', '=', Employee.id),
																('cts_id.fiscal_year_id.name', '=', last_date['last_year']),
																('cts_id.type', '=', last_date['last_type']),
																('less_than_one_month', '=', True)
																]).total_cts
			# Remuneracion desde la planilla 
			#wage = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.basic_sr_id).total
			# Toma del contrato
			wage = MonthSlip.employee_wage
			household_allowance = MonthSlip.line_ids.filtered(lambda line: line.salary_rule_id == MainParameter.household_allowance_sr_id).total
			bonus_months = len(Lots.mapped('slip_ids').filtered(lambda slip: slip.employee_id == Employee))
			for Lot in Lots:
				admission_payslip_date = date(admission_date.year, admission_date.month, 1)
				EmployeeSlips = Lot.slip_ids.filtered(lambda slip: slip.employee_id == Employee and
																   slip.date_from >= admission_payslip_date and
																   slip.date_to <= MonthSlip.date_to)
				SalaryRules = EmployeeSlips.mapped('line_ids')
				WorkedDays = EmployeeSlips.mapped('worked_days_line_ids')
				WorkingWD =	sum(WorkedDays.filtered(lambda line: line.wd_type_id in MainParameter.working_wd_ids).mapped('number_of_days'))
				if WorkingWD >= 30:
					months += 1
				else:
					days += WorkingWD
				LackWD = sum(WorkedDays.filtered(lambda line: line.wd_type_id == MainParameter.lack_wd_id).mapped('number_of_days'))
				lacks += LackWD
				Commissions += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.commission_sr_ids and line.total > 0)
				Bonus += SalaryRules.filtered(lambda line: line.salary_rule_id in MainParameter.bonus_sr_ids and line.total > 0)
				ExtraHours += SalaryRules.filtered(lambda line: line.salary_rule_id == MainParameter.extra_hours_sr_id and line.total > 0)
			if record_type in ['07', '12']:
				days = days if record.months_and_days else 0
			if self._context.get('commission'):
				commission = self._context.get('commission')
			else:
				commission = self.calculate_bonus(admission_date, date_from, bonus_months, Commissions)
			bonus = self.calculate_bonus(admission_date, date_from, bonus_months, Bonus)
			if self._context.get('extra_hours'):
				extra_hours = self._context.get('extra_hours')
			else:
				extra_hours = self.calculate_bonus(admission_date, date_from, bonus_months, ExtraHours)
			computable_remuneration = wage + household_allowance + commission + bonus + extra_hours
			divider = 6 if record_type in ['07', '12'] else 12
			if record_type in ['05', '11']:
				if liquidation:
					cessation_date = MonthSlip.contract_id.date_end
					#####Logic to get 1/6 of gratification in diferent situations taken the deposit_date as reference
					GratificationLines = self.env['hr.gratification.line'].search([('employee_id', '=', Employee.id),
																				   ('gratification_id.fiscal_year_id.name', '=', str(year))
																				]).sorted(lambda line: line.gratification_id.deposit_date)
					if len(GratificationLines) == 0:
						required_gratification = {'year': str(year - 1), 'month': '12'}
					if len(GratificationLines) == 1:
						if GratificationLines.gratification_id.deposit_date <= cessation_date:
							required_gratification = {'year': str(year), 'month': '07'}
						else:
							required_gratification = {'year': str(year - 1), 'month': '12'}
					if len(GratificationLines) == 2:
						if GratificationLines[0].gratification_id.deposit_date <= cessation_date and \
						   cessation_date < GratificationLines[1].gratification_id.deposit_date:
							required_gratification = {'year': str(year), 'month': '07'}
						if cessation_date >= GratificationLines[1].gratification_id.deposit_date:
							required_gratification = {'year': str(year), 'month': '12'}
				GratificationLine = self.env['hr.gratification.line'].search([('employee_id', '=', Employee.id),
																			  ('gratification_id.fiscal_year_id.name', '=', required_gratification['year']),
																			  ('gratification_id.type', '=', required_gratification['month'])
																			])
				if self._context.get('sixth_of_gratification'):
					sixth_of_gratification = self._context.get('sixth_of_gratification')
				else:
					sixth_of_gratification = ReportBase.custom_round(GratificationLine.total_grat/6, 2) if GratificationLine else 0
				computable_remuneration += sixth_of_gratification

			amount_per_month = computable_remuneration/divider if MonthSlip.contract_id.labor_regime == 'general' else computable_remuneration/(divider * 2)
			amount_per_day = amount_per_month/30
			vals = {
					'employee_id': Employee.id,
					'contract_id': MonthSlip.contract_id.id,
					'admission_date': admission_date,
					'months': months,
					'days': days,
					'lacks': lacks,
					'wage': wage,
					'household_allowance': household_allowance,
					'commission': commission,
					'bonus': bonus,
					'extra_hours': extra_hours,
					'computable_remuneration': computable_remuneration,
					'amount_per_month': ReportBase.custom_round(amount_per_month, 2),
					'amount_per_day': ReportBase.custom_round(amount_per_day, 2)
				}
			if record_type in ['07', '12']:
				if liquidation:
					vals['compute_date'] = admission_date if admission_date > date_from else date_from
					vals['cessation_date'] = MonthSlip.contract_id.date_end
					vals['liquidation_id'] = record.id
				else:
					vals['gratification_id'] = record.id
				amount_per_lack = amount_per_day * lacks
				grat_per_month = ReportBase.custom_round(amount_per_month * months, 2)
				grat_per_day = ReportBase.custom_round(amount_per_day * days, 2)
				total_grat = ReportBase.custom_round((grat_per_month + grat_per_day) - amount_per_lack, 2)
				percent = MonthSlip.contract_id.social_insurance_id.percent or 0 if record.with_bonus else 0
				bonus_essalud = ReportBase.custom_round(total_grat * percent * 0.01, 2)
				total = ReportBase.custom_round(total_grat + bonus_essalud, 2)
				vals['amount_per_lack'] = ReportBase.custom_round(amount_per_lack, 2)
				vals['grat_per_month'] = grat_per_month
				vals['grat_per_day'] = grat_per_day
				vals['total_grat'] = total_grat
				vals['bonus_essalud'] = bonus_essalud
				vals['total'] = total
				if liquidation:
					Grat = self.env['hr.gratification'].search([('payslip_run_id', '=', liquidation.payslip_run_id.id), 
																('fiscal_year_id', '=', liquidation.fiscal_year_id.id),
																('type', '=', record_type),
																('company_id', '=', liquidation.company_id.id)])
					if Grat and Grat.line_ids.filtered(lambda line: line.employee_id == Employee.id):
						continue
					else:
						self.env['hr.gratification.line'].create(vals)
				else:
					self.env['hr.gratification.line'].create(vals)
			else:
				if liquidation:
					vals['compute_date'] = admission_date if admission_date > date_from else date_from
					vals['cessation_date'] = MonthSlip.contract_id.date_end
					vals['liquidation_id'] = record.id
				else:
					vals['cts_id'] = record.id
				medical_days, excess_medical_rest = self.calculate_excess_medical_rest(year, Employee, cts_year=True)
				if excess_medical_rest>0:
					lacks=lacks+excess_medical_rest
					vals['lacks'] = lacks
				# days = days + medical_days
				# if days >= 30:
				# 	days, months = MainParameter.get_months_of_30_days(days, months)
				# vals['months'] = months
				# vals['days'] = days
				amount_per_lack = amount_per_day * (lacks + excess_medical_rest)
				cts_per_month = ReportBase.custom_round(amount_per_month * months, 2)
				cts_per_day = ReportBase.custom_round(amount_per_day * days, 2)
				cts_soles = ReportBase.custom_round(cts_per_month + cts_per_day - amount_per_lack + remaining_wage, 2)
				total_cts = cts_soles
				cts_dollars = ReportBase.custom_round(total_cts/record.exchange_type, 2)
				vals['less_than_one_month'] = True if months == 0 and days > 0 else False
				vals['exchange_type'] = record.exchange_type
				vals['excess_medical_rest'] = excess_medical_rest
				vals['sixth_of_gratification'] = sixth_of_gratification
				vals['amount_per_lack'] = ReportBase.custom_round(amount_per_lack, 2)
				vals['cts_per_month'] = cts_per_month
				vals['cts_per_day'] = cts_per_day
				vals['cts_soles'] = cts_soles
				vals['total_cts'] = total_cts
				vals['cts_dollars'] = cts_dollars
				if liquidation:
					CTS = self.env['hr.cts'].search([('payslip_run_id', '=', liquidation.payslip_run_id.id), 
													 ('fiscal_year_id', '=', liquidation.fiscal_year_id.id),
													 ('type', '=', record_type),
													 ('company_id', '=', liquidation.company_id.id)])
					if CTS and CTS.line_ids.filtered(lambda line: line.employee_id == Employee.id):
						continue
					else:
						self.env['hr.cts.line'].create(vals)
				else:
					self.env['hr.cts.line'].create(vals)
