# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate


class HrUtilitiesPrintWizard(models.TransientModel):
    _inherit = 'hr.utilities.print.wizard'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company.id)

    def get_print(self):
        data = dict()
        data['hr_utilities_id'] = self.hr_utilities_id.id
        data['hr_utilities_line_id'] = self.hr_utilities_line_id.id
        data['mode'] = self.mode
        return self.env.ref('fxo_hr_utilities_it.report_hr_utilities_it_all_id').with_context(
            landscape=False).report_action(self,
                                          data=data)
