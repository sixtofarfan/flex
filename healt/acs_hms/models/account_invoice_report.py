# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    department_id = fields.Many2one('hr.department', string='Departamento', readonly=True)
    patient_id = fields.Many2one('hms.patient', string='Paciente', readonly=True)
    physician_id = fields.Many2one('hms.physician', string='Medico', readonly=True)
    ref_physician_id = fields.Many2one('res.partner', string='Medico Referido', readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += """
            , line.department_id as department_id, line.patient_id as patient_id, line.physician_id as physician_id, line.ref_physician_id as ref_physician_id
            """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()
        select_str += """
            , line.department_id, line.patient_id, line.physician_id, line.ref_physician_id
            """
        return select_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ", line.department_id, line.patient_id, line.physician_id, line.ref_physician_id"
        return group_by_str
