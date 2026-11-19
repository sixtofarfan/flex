# -*- coding: utf-8 -*-


from odoo import models, fields
from datetime import date


class PaymentEfficiencyWizard(models.TransientModel):
    _name = 'payment.efficiency.wizard'

    def _get_date(self):
        return date.today()

    report_date = fields.Date(string='Report Create Date', readonly=True, default=_get_date)

    def generate_report_xlsx(self):
        data = {
            'report_date': self.report_date,
        }
        return self.env.ref('fxo_account_payment_efficiency.payment_efficiency_xlsx').report_action([],
                                                                                                           data=data)
