# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date
from odoo.addons.payment.models.payment_acquirer import ValidationError


class WizardReport(models.TransientModel):
    _name = "wizard.report.suscrip"

    def _default_fiscal_year(self):
        current_date = date.today()
        fiscal_year = self.env['account.fiscal.year'].search(
            [('date_from', '<=', current_date), ('date_to', '>=', current_date)])
        if len(fiscal_year) > 0:
            return fiscal_year[0].id

    fiscal_year_id = fields.Many2one('account.fiscal.year', string='Fiscal Year', default=_default_fiscal_year,
                                     required=True)
    period_id = fields.Many2one('account.period',
                                string='Period',
                                required=True,
                                domain="[('close','=',False), ('is_opening_close','=',False),('fiscal_year_id','=',fiscal_year_id)]")
    name = fields.Char(related='period_id.name', string='Period Name')
    date_start = fields.Date(related='period_id.date_start', string='Start date')
    date_end = fields.Date(related='period_id.date_end', string='End date')

    @api.onchange('fiscal_year_id')
    def _onchange_fiscal_year_id(self):
        if self.fiscal_year_id:
            self.period_id = None

    def view_report(self):
        domain = list()
        sql_data = """
                SELECT sbl.service_id  FROM public.sale_subscription_line  sbl
                LEFT JOIN sale_subscription ss ON (ss.id=sbl.analytic_account_id)
                LEFT JOIN sale_subscription_stage sss ON (sss.id=ss.stage_id)
                LEFT JOIN res_company rc ON (ss.company_id=rc.id)
                where rc.id = %d  and sbl.state ='done' and sbl.price_subtotal > 0 
                and substring(to_char(sbl.stop_date,'YYYY-MM-DD'),1,7) <= %s
                and sss.in_progress = True and 
                sbl.service_id not in 
                (SELECT aml.service_id from account_move_line aml
                LEFT JOIN res_company rc ON (aml.company_id=rc.id)
                LEFT JOIN account_move am ON (am.id = aml.move_id)
                LEFT JOIN account_period ap ON (ap.id = am.invoice_period_id)
                where am.invoice_period_id = %d and rc.id=%d and aml.service_id is not null) order by sbl.stop_date
        """ % (self.env.company.id, "'" + str(self.period_id.date_start)[0:8] + "'", self.period_id.id,
               self.env.company.id)

        self._cr.execute(sql_data)
        subcription_line_ids = self._cr.dictfetchall()
        subcription_line_ids = [x['service_id'] for x in subcription_line_ids]

        if len(subcription_line_ids) == 1:
            sql_update_period = """
                UPDATE public.sale_subscription_line
                    SET period_report_id=%d, name_period = %s
                    WHERE service_id = %s;
            """ % (self.period_id.id, "'"+self.period_id.name+"'", "'"+subcription_line_ids[0]+"'")
        else:
            subscription_tuple = tuple(subcription_line_ids)
            sql_update_period = """
                            UPDATE public.sale_subscription_line
                                SET period_report_id=%d, name_period = %s
                                WHERE service_id in %s;
                        """ % (self.period_id.id, "'"+self.period_id.name+"'", subscription_tuple)
        self._cr.execute(sql_update_period)

        domain.append(('service_id', 'in', subcription_line_ids))
        view = self.env.ref('report_invoice_suscription_js_fxo.sale_subscription_line_tree', False)
        return {
            'name': _('Reporte Suscripcion - Facturaciòn'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'sale.subscription.line',
            'view_id': view.id,
            'domain': domain,
            'context': {'search_default_by_name_period': 1, 'search_default_by_stop_date': 1},

        }
