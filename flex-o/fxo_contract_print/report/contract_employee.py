# -*- coding: utf-8 -*-

import time

import odoo.addons.decimal_precision as dp
from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import Warning

from jinja2 import Template


class report_sale_subscription_contract(models.AbstractModel):
    _name = 'report.fxo_contract_print.report_sale_subscription_contract'

    @api.model
    def render_html(self, docids, data=None):

        report_obj = self.env['report']
        self.model = self.env.context.get('active_model')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': self.env['sale.subscription'].browse(docids),
            'time': time,
            'fecha_str': self._fecha_str,
            'conversion': self._conversion,

        }
        return report_obj.render('fxo_contract_print.report_sale_subscription_contract', docargs)


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

        row = self.env['sale.subscription'].browse(code)

        #### Codigo de prueba
        direccion=""

        if row.employee_id.personal_street:
            direccion = row.employee_id.personal_street 
        else:
            direccion = direccion

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
        Contracts = row.employee_id.contract_ids
        LastContract = max(Contracts, key=Contracts.date_start)
        fields = {
            'nombre_contrato': row.name if row.name else "",
            'nombre_empleado': row.employee_id.name if row.employee_id.name else "",
            'direccion_empleado': direccion,
            'tipo_documento': row.employee_id.type_document_partner_it.name if row.employee_id.type_document_partner_it.name else "",
            'nro_documento': row.employee_id.nro_documento if row.employee_id.nro_documento else "",
            'titulo_trabajo': row.job_id.name if row.job_id.name else "",
            'salario': '{0:.2f}'.format(row.wage),
            'moneda': "SOLES",
            'nombre_cliente': row.analytic_account_id.partner_id.name if row.analytic_account_id.partner_id.name else "",
            'tarea': row.task_id.name if row.task_id.name else "",
            'fecha_inicio': row.employee_id.emp_date_start if row.employee_id.emp_date_start else "",
            'fecha_fin': LastContract.date_end if LastContract.date_end else "",
            'plazo_meses': self.get_num_month(datetime.strptime(row.date_start, '%Y-%m-%d'), datetime.strptime(row.date_end, '%Y-%m-%d')),
        }

        return jinga_html_template.render(**fields)
