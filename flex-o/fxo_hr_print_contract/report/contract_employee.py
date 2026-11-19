# -*- coding: utf-8 -*-

import time

import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import UserError
import calendar

from jinja2 import Template
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import arrow
except:
    install('arrow')



class report_contract_employee(models.AbstractModel):
    _name = 'report.fxo_hr_print_contract.report_contract_employee'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.contract'].browse(docids)
        for doc in docs:
            if not doc.template_id:
                raise UserError('No se puede generar un reporte si no se ha definido una Plantilla para el contrato')
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.contract',
            'data': data,
            'docs': docs,
            'conversion': self._conversion,
        }

    def _fecha_str(self, city):

        date = time.strftime("%Y-%m-%d")
        day = time.strftime('%d', time.strptime(date,'%Y-%m-%d'))
        month = time.strftime('%B', time.strptime(date,'%Y-%m-%d')).upper()
        year = time.strftime('%Y', time.strptime(date,'%Y-%m-%d'))
        fecha = str(city).upper() + " , " + " " + day + " de " + month + " del " + year

        return fecha

    def get_num_month(self, start,end):
        num_month = 0
        for d in arrow.Arrow.range('month',start,end):
            num_month +=1
        return num_month

    def _conversion(self, template, code):
        #template = 'Hey, my name is {{ custom_function(first_name) }}'
        jinga_html_template = Template(template)
        #jinga_html_template.globals['custom_function'] = custom_function

        row = self.env['hr.contract'].browse(code)
        #### Codigo de prueba
        """
        direccion=""

        if row.employee_id.personal_state_id.name:
            direccion = direccion+ " / "+row.employee_id.personal_state_id.name 
        else:
            direccion = direccion

        if row.employee_id.personal_province_id.name:
            direccion = direccion+" / "+row.employee_id.personal_province_id.name 
        else:
            direccion = direccion

        if row.employee_id.personal_district_id.name:
            direccion = direccion+ " / "+row.employee_id.personal_district_id.name
        else:
            direccion = direccion
        """
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        if row.date_start:
            date_start = '{0} de {1} del {2}'.format(
                row.date_start.day,
                MainParameter.get_month_name(row.date_start.month),
                row.date_start.year,
                )
        else:
            date_start = ''
        if row.date_end:
            date_end = '{0} de {1} del {2}'.format(
                row.date_end.day,
                MainParameter.get_month_name(row.date_end.month),
                row.date_end.year,
                )
        else:
            date_end = ''
        if row.date_start and row.date_end:
            months = (row.date_end.year - row.date_start.year) * 12 + row.date_end.month - row.date_start.month
            days = row.date_end.day - row.date_start.day + 1
            if days < 0:
                days = 0
            months = '%s mes(es) y %s dia(as)' % (str(months), str(days))
        else:
            months = 'indefinido'
        letter_Wage = MainParameter.number_to_letter(row.wage)
        fields = {
            'nombre_contrato': row.name if row.name else "",
            'nombre_empleado': row.employee_id.name if row.employee_id.name else "",
            'direccion_empleado': row.employee_id.address if row.employee_id.address else "",
            'tipo_documento': row.employee_id.type_document_id.name if row.employee_id.type_document_id.name else "" ,
            'nro_documento': row.employee_id.identification_id if row.employee_id.identification_id else "" ,
            'titulo_trabajo': row.job_id.name if row.job_id.name else "",
            'salario': str('{0:.2f}'.format(row.wage)),
            'salario_letras': letter_Wage,
            'moneda': "SOLES",
            'nombre_cliente': row.analytic_account_id.partner_id.name if row.analytic_account_id.partner_id.name else "" ,
            #'tarea': row.task_id.name if row.task_id.name else "",
            'meses': months,
            'fecha_inicio': date_start,
            'fecha_fin': date_end,
            'fecha_prueba_fin': row.trial_date_end,
            'fecha_ingreso_trabajador': row.employee_id.emp_date_start if row.employee_id.emp_date_start else '',
            'funciones_empleado': row.notes if row.notes else "",
            #'plazo_meses': self.get_num_month(datetime.strptime(row.date_start, '%Y-%m-%d'), datetime.strptime(row.date_end, '%Y-%m-%d')),
        }

        return jinga_html_template.render(**fields)
