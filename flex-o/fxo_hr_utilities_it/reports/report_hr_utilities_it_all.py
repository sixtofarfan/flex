# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date


class ReportHrUtilitiesItAll(models.AbstractModel):
    _name = 'report.fxo_hr_utilities_it.report_hr_utilities_it_all'

    @api.model
    def _get_report_values(self, docids, data=None):
        utilities_report = self.env['ir.actions.report']._get_report_from_name(
            'fxo_hr_utilities_it.report_hr_utilities_it_all')
        hr_utilities_id = data['hr_utilities_id']
        hr_utilities_line_id = data['hr_utilities_line_id']
        MainParameter = self.env['hr.main.parameter'].get_main_parameter()
        mode = data['mode']
        current_date = date.today()
        format_date = "%A, %d de %B %Y"
        if mode == 'all':
            hr_utilities = self.env['hr.utilities.it.line'].search([('main_id', '=', hr_utilities_id)])
        else:
            hr_utilities = self.env['hr.utilities.it.line'].search([('id', '=', hr_utilities_line_id)])
        return {
            'doc_ids': self.ids,
            'doc_model': utilities_report.model,
            'docs': hr_utilities,
            'date_current': str(current_date.strftime(format_date)).split(',')[1],
            'legal_representative': MainParameter.legal_representative.upper()
        }
