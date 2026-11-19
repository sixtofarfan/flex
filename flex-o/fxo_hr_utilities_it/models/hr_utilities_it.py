# -*- coding:utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import requests
from base64 import encodestring


class HrUtilitiesIt(models.Model):
    _inherit = 'hr.utilities.it'

    def calculate(self):
        self._change_percentage_rent()
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        MainParameter.check_utility_values()
        self.env.cr.execute(
            self._get_sql_utlities(MainParameter.rule_total_income, MainParameter.wd_dtrab, MainParameter.wd_falt))
        res = self.env.cr.dictfetchall()
        for elem in res:
            contract_hr = self.env['hr.contract'].search([('employee_id', '=', elem['employee_id']),
                                                          ('company_id', '=', self.company_id.id)],
                                                         order='date_start desc')
            if len(contract_hr) > 0:
                if contract_hr[0].distribution_id.name == elem['distribution_id']:
                    self.env['hr.utilities.it.line'].create({
                        'main_id': self.id,
                        'employee_document': elem['employee_document'],
                        'employee': elem['employee'],
                        'employee_id': elem['employee_id'],
                        'distribution_id': elem['distribution_id'],
                        # 'contract_id' : elem['contract_id'],
                        'salary': elem['sueldos'],
                        'number_of_days': elem['dias'],
                    })

        for j in self.utilities_line_ids:
            self.sum_salary_year += j.salary
            self.sum_number_of_days_year += j.number_of_days
        self.factor_salary = (self.distribution * 0.50) / self.sum_salary_year
        self.factor_number_of_days = (self.distribution * 0.50) / self.sum_number_of_days_year
        tot_salary, tot_days = 0, 0
        for i in self.utilities_line_ids:
            i.for_salary = round(i.salary * self.factor_salary, 2)
            tot_salary += i.for_salary
            i.for_number_of_days = round(i.number_of_days * self.factor_number_of_days, 2)
            tot_days += i.for_number_of_days

        # ROUND SALARY
        diff = 0
        if tot_salary < (self.distribution * 0.50):
            diff = (self.distribution * 0.50) - tot_salary
            self.utilities_line_ids[len(self.utilities_line_ids) - 1].for_salary = self.utilities_line_ids[
                                                                                       len(self.utilities_line_ids) - 1].for_salary + diff
        if tot_salary > (self.distribution * 0.50):
            diff = tot_salary - (self.distribution * 0.50)
            self.utilities_line_ids[len(self.utilities_line_ids) - 1].for_salary = self.utilities_line_ids[
                                                                                       len(self.utilities_line_ids) - 1].for_salary - diff

        # ROUND NUMBER OF DAYS
        diff = 0
        if tot_days < (self.distribution * 0.50):
            diff = (self.distribution * 0.50) - tot_days
            self.utilities_line_ids[len(self.utilities_line_ids) - 1].for_number_of_days = self.utilities_line_ids[
                                                                                               len(self.utilities_line_ids) - 1].for_number_of_days + diff
        if tot_days > (self.distribution * 0.50):
            diff = tot_days - (self.distribution * 0.50)
            self.utilities_line_ids[len(self.utilities_line_ids) - 1].for_number_of_days = self.utilities_line_ids[
                                                                                               len(self.utilities_line_ids) - 1].for_number_of_days - diff

        for i in self.utilities_line_ids:
            if i.for_number_of_days and i.for_salary:
                i.total_utilities = i.for_number_of_days + i.for_salary
        self.state = 'calculate'

    def _get_sql_utlities(self, rule_total_income, wd_dtrab, wd_falt):
        sql = """
                SELECT distinct coalesce(he.identification_id, '') as employee_document, he.name as employee, he.id as employee_id,had.name as distribution_id, T1.sueldos, T2.dias FROM hr_contract hc
                LEFT JOIN hr_analytic_distribution had on had.id = hc.distribution_id
                LEFT JOIN hr_employee he ON he.id = hc.employee_id
                LEFT JOIN (
                SELECT hp.employee_id,sum(hpl.total) as sueldos FROM hr_payslip_line hpl
                LEFT JOIN hr_payslip hp ON hp.id = hpl.slip_id
                WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                    to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND 
                    hpl.salary_rule_id = {salary_rule_id} AND
                    hp.company_id = {company_id}                
                GROUP BY hp.employee_id
                ) T1 ON T1.employee_id = hc.employee_id
                LEFT JOIN (
                
                SELECT t5.employee_id,t5.dias -t6.dias as dias from(
                
                SELECT t1.employee_id,t1.dias - t2.dias as dias  FROM(
                SELECT hp.employee_id,sum(hpwd.number_of_days) as dias FROM hr_payslip_worked_days hpwd
                LEFT JOIN hr_payslip hp ON hp.id = hpwd.payslip_id
                WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                    to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND 
                    hpwd.wd_type_id in ({wd_dtrab}) AND
                    hp.company_id = {company_id}
                group by hp.employee_id)t1
                LEFT JOIN(
                SELECT hp.employee_id,sum(hpwd.number_of_days) as dias FROM hr_payslip_worked_days hpwd
                LEFT JOIN hr_payslip hp ON hp.id = hpwd.payslip_id
                WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                    to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND 
                    hpwd.wd_type_id in ({wd_falt}) AND
                    hp.company_id = {company_id}
                group by hp.employee_id)t2 ON t1.employee_id = t2.employee_id
                
                )t5
                LEFT JOIN(
                SELECT hp.employee_id,coalesce(sum(hp.holidays),0) as dias FROM hr_payslip hp
                WHERE to_char(hp.date_from::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                    to_char(hp.date_to::timestamp with time zone, 'yyyy'::text) = '{year}' AND
                    hp.company_id = {company_id}
                group by hp.employee_id)t6 ON t5.employee_id = t6.employee_id
                
                ) T2 ON T2.employee_id = hc.employee_id
                WHERE T1.sueldos is not null AND T2.dias is not null
                AND hc.company_id = {company_id}
                AND hc.labor_regime IN ('general','small')
                """.format(
            year=self.fiscal_year_id.name,
            salary_rule_id=str(rule_total_income.id),
            wd_dtrab=','.join(str(i) for i in wd_dtrab.ids),
            wd_falt=','.join(str(i) for i in wd_falt.ids),
            company_id=str(self.company_id.id)
        )
        return sql

    def send_email_utilities(self):
        # for res in self:
        #     for line in res.utilities_line_ids:
        #         line.send_email_utilities()
        return self.send_email_utilities_wizard()

    def send_email_utilities_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "send.email.utilities.wizard",
            "views": [(False, "form")],
            "context": self._context,
            "name": "Envio de Utilidades por Correo",
            "target": "new",
        }


class HrUtilitiesItLine(models.Model):
    _inherit = 'hr.utilities.it.line'
    _rec_name = 'employee_id'

    def send_email(self, template):
        email_context = self.env.context.copy()
        attachment_ids = self.get_xml_pdf()
        email_context.update({
            'email_to': self.employee_id.work_email,
            'default_attachment_ids': [(6, 0, attachment_ids)],
        })
        template.with_context(email_context).send_mail(self.id)
        return True

    def get_xml_pdf(self):
        attach = {}
        attachment_ids = []
        data = {
            'hr_utilities_id': self.main_id.id,
            'mode': 'one',
            'hr_utilities_line_id': self.id}

        result_pdf, type = self.env['ir.actions.report']._get_report_from_name(
            'fxo_hr_utilities_it.report_hr_utilities_it_all').render_qweb_pdf(self.id, data)
        attach['name'] = "Liquidación de Utilidades de %s.pdf" % self.employee
        attach['type'] = "binary"
        attach['datas'] = encodestring(result_pdf)
        attach['res_model'] = "mail.compose.message"
        attachment_id = self.env['ir.attachment'].create(attach)
        attachment_ids.append(attachment_id.id)
        return attachment_ids
