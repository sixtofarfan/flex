# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools

class HrPayslipRunWdView(models.Model):
	_name = 'hr.payslip.run.wd.view'
	_auto = False

	employee_id = fields.Many2one('hr.employee', string='Empleado')
	identification_id = fields.Char(string='Nro. Documento')
	date_start = fields.Char(string='Fecha Inicio')
	membership = fields.Char(string='Afiliacion')
	department = fields.Char(string='Departamento')
	worker_type = fields.Char(string='Tipo de Trabajador')
	job = fields.Char(string='Puesto de Trabajo')
	analytic_account = fields.Char(string='Cuenta Analitica')
	distribution = fields.Char(string='Distribucion Analitica')
	membership = fields.Char(string='Afiliacion')
	social_insurance = fields.Char(string='Seguro Social')
	workday = fields.Char(string='Jornada Laboral')
	labor_regime = fields.Selection([
		('general', 'Regimen General'),
		('small', 'Pequeña Empresa'),
		('micro', 'Micro Empresa'),
		('practice', 'Practicante'),
		('fourth-fifth', 'Trabajadores de 4ta-5ta'),
	], string='Regimen Laboral')
	payslip_run_id = fields.Many2one('hr.payslip.run', string='Lote')
	payslip_id = fields.Many2one('hr.payslip', string='Nomina')
	structure_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial')
	calendar_id = fields.Many2one('resource.calendar', string='Planificacion de Trabajo')
	template_id = fields.Many2one('hr.contract.template', string='Plantilla de Contrato')
	commision_type = fields.Selection([
		('flow', 'Flujo'),
		('mixed', 'Mixta'),
	], string='Tipo de Comision')
	situation = fields.Char(string='Situacion')
	sctr = fields.Char(string='SCTR')
	worked_day = fields.Char(string='Worked Day')
	days = fields.Float(string='Dias')
	hours = fields.Float(string='Horas')
	company_id = fields.Many2one('res.company', string='Compañia')

	def get_payslip_run_wd_view(self):
		self.init()
		return {
			'name': 'Analisis de Dias Laborados',
			'type': 'ir.actions.act_window',
			'view_mode': 'pivot,graph,tree',
			'res_model': 'hr.payslip.run.wd.view',
			'views': [
				[False, 'pivot'],
				[False, 'graph'],
				[False, 'tree'],
			],
		}

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		sql = """
		CREATE OR REPLACE VIEW hr_payslip_run_wd_view AS ( 
			{0} {1} {2} {3} {4}
		)
		""".format(
			self._select(),
			self._from(),
			self._where(),
			self._group_by(),
			self._order_by(),
		)
		self._cr.execute(sql)

	def _select(self):
		sql = """
		select
		row_number() OVER () AS id,
		he.id as employee_id,
		he.identification_id,
		hc.date_start,
		hd.name as department,
		hwt.name as worker_type,
		hj.name as job,
		('[' || aaa.code || ']' || aaa.name) as analytic_account,
		had.name as distribution,
		hm.name as membership,
		hsi.name as social_insurance,
		hw.name as workday,
		hc.labor_regime as labor_regime,
		hpr.id as payslip_run_id,
		hp.id as payslip_id,
		hc.resource_calendar_id as calendar_id,
		hc.structure_id as structure_id,
		hc.template_id as template_id,
		hc.commision_type as commision_type,
		hs.name as situation,
		hsctr.name as sctr,
		hpwd.name as worked_day,
		sum(hpwd.number_of_days) as days,
		sum(hpwd.number_of_hours) as hours,
		hc.company_id as company_id
		"""
		return sql

	def _from(self):
		sql = """
		from hr_payslip hp
		left join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
		inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
		inner join hr_employee he on he.id = hp.employee_id
		inner join hr_contract hc on hc.id = hp.contract_id
		left join hr_department hd on hd.id = hc.department_id
		left join hr_worker_type hwt on hwt.id = hc.worker_type_id
		left join hr_job hj on hj.id = hc.job_id
		left join account_analytic_account aaa on aaa.id = hc.analytic_account_id
		left join hr_analytic_distribution had on had.id = hc.distribution_id
		left join hr_membership hm on hm.id = hc.membership_id
		left join hr_social_insurance hsi on hsi.id = hc.social_insurance_id
		left join hr_workday hw on hw.id = hc.workday_id
		left join hr_situation hs on hs.id = hc.situation_id
		left join hr_sctr hsctr on hsctr.id = hc.sctr_id
		"""
		return sql

	def _where(self):
		sql = """
		where hpr.company_id = {0}
		""".format(self.env.company.id)
		return sql

	def _group_by(self):
		sql = """
		group by 
		he.identification_id, 
		he.id, 
		hc.date_start,  
		hm.name,
		hd.name,
		hwt.name,
		hj.name,
		hd.name,
		hwt.name,
		hj.name,
		aaa.name,
		aaa.code,
		had.name,
		hm.name,
		hsi.name,
		hw.name,
		hc.labor_regime,
		hpr.id,
		hp.id,
		hc.resource_calendar_id,
		hc.structure_id,
		hc.template_id,
		hc.commision_type,
		hs.name,
		hsctr.name,
		hpwd.name,
		hc.company_id
		"""
		return sql

	def _order_by(self):
		sql = """
		order by he.identification_id
		"""
		return sql