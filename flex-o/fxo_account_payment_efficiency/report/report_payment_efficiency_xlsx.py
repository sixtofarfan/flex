# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields
from datetime import timedelta, time
from odoo.tools.float_utils import float_round


class PaymentEfficiencyXlsx(models.AbstractModel):
    _name = 'report.fxo_account_payment_efficiency.payment_efficiency_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        report_date = data['report_date']
        company_id = self.env.user.company_id.id
        dicc_month = {
            '1': 'ENE',
            '2': 'FEB',
            '3': 'MAR',
            '4': 'ABR',
            '5': 'MAY',
            '6': 'JUN',
            '7': 'JUL',
            '8': 'AGO',
            '9': 'SEP',
            '10': 'OCT',
            '11': 'NOV',
            '12': 'DIC'
        }
        sql_periods = """
            Select result.year_invoice::VARCHAR, result.month_invoice::VARCHAR, sum(result.amount_total) as amount_total from
                (SELECT invoice_date, Extract(year FROM invoice_date) as year_invoice, Extract(month FROM invoice_date) 
                as month_invoice, sum(amount_total_signed) as amount_total
                FROM account_move
                where company_id=%d and state='posted' and type='out_invoice' group by year_invoice, invoice_date
                order by invoice_date desc) as result group by result.year_invoice, result.month_invoice 
                order by result.year_invoice desc, result.month_invoice desc;
        """ % company_id
        self._cr.execute(sql_periods)
        periods = self._cr.fetchall()
        sheet = workbook.add_worksheet('Informe Eficiencia')
        col = 1
        sheet.set_column(0, 0, 40)
        style_period = workbook.add_format({'bold': 1,
                                            'border': 1,
                                            'align': 'center',
                                            'valign': 'vcenter',
                                            'font': {'size': 11},
                                            'fg_color': '#4472C4',
                                            'font_color': 'white',
                                            'text_wrap': True})
        style_report_date = workbook.add_format({'bold': 1,
                                                 'border': 1,
                                                 'align': 'center',
                                                 'valign': 'vcenter',
                                                 'font': {'size': 11},
                                                 'text_wrap': True})
        style_credit_note = workbook.add_format({'bold': 1,
                                                 'border': 1,
                                                 'align': 'left',
                                                 'valign': 'vcenter',
                                                 'font_color': 'red',
                                                 'font': {'size': 11},
                                                 'text_wrap': True})
        style_credit_note_right = workbook.add_format({'border': 1,
                                                       'align': 'right',
                                                       'valign': 'vcenter',
                                                       'font_color': 'red',
                                                       'font': {'size': 11},
                                                       'text_wrap': True})
        style_invoice = workbook.add_format({'bold': 1,
                                             'border': 1,
                                             'align': 'right',
                                             'valign': 'vcenter',
                                             'font': {'size': 11},
                                             'text_wrap': True})
        style_invoice_left = workbook.add_format({'bold': 1,
                                                  'border': 1,
                                                  'align': 'left',
                                                  'valign': 'vcenter',
                                                  'font': {'size': 11},
                                                  'text_wrap': True})
        style_payment_right = workbook.add_format({'border': 1,
                                                   'align': 'right',
                                                   'valign': 'vcenter',
                                                   'font': {'size': 11},
                                                   'text_wrap': True})
        style_cobranza_left = workbook.add_format({'bold': 1,
                                                   'border': 1,
                                                   'align': 'left',
                                                   'valign': 'vcenter',
                                                   'font': {'size': 11},
                                                   'font_color': 'orange',
                                                   'text_wrap': True})
        style_cobranza_right = workbook.add_format({'bold': 1,
                                                    'border': 1,
                                                    'align': 'right',
                                                    'valign': 'vcenter',
                                                    'font': {'size': 11},
                                                    'font_color': 'orange',
                                                    'text_wrap': True})
        style_ingreso_net = workbook.add_format({'bold': 1,
                                                 'border': 1,
                                                 'align': 'left',
                                                 'valign': 'vcenter',
                                                 'font': {'size': 11},
                                                 'font_color': 'green',
                                                 'text_wrap': True})
        style_ingreso_right = workbook.add_format({'bold': 1,
                                                   'border': 1,
                                                   'align': 'right',
                                                   'valign': 'vcenter',
                                                   'font': {'size': 11},
                                                   'font_color': 'green',
                                                   'text_wrap': True})
        sheet.merge_range(0, col, 0, len(periods),
                          'PERIODO',
                          style_period)
        sheet.set_row(0, 35)
        sheet.write(0, 0, 'Fecha de reporte: ' + report_date, style_report_date)
        sheet.write(2, 0, 'Facturación + Impuestos', style_invoice_left)
        sql_internal_type = """
            SELECT eci.name, am.internal_type_id
                FROM account_move am
                LEFT JOIN einvoice_catalog_09_internal eci ON (am.internal_type_id=eci.id)
                where am.company_id=%d and am.state='posted' and am.type='out_refund' 
                and internal_type_id is not null
                group by eci.name, internal_type_id;
        """ % company_id
        self._cr.execute(sql_internal_type)
        internal_types = self._cr.fetchall()
        ingreso_list = list()
        payment_list = list()
        j = 1
        for p in periods:
            sheet.set_column(col, col, 20)
            sheet.write(1, col, dicc_month[p[1]] + '-' + p[0], style_period)
            sheet.write(2, col, '{0:.2f}'.format(p[2]).replace('.', ','), style_invoice)
            row = 3
            value_total = 0
            for t in internal_types:
                sheet.write(row, 0, 'Nota de crédito/' + t[0], style_credit_note)
                value = self.search_value_period_type(t[1], p[0], p[1], company_id)
                if len(value) == 1:
                    if value[0][0]:
                        value_total += value[0][0]
                        sheet.write(row, col, '{0:.2f}'.format(value[0][0]).replace('.', ','), style_credit_note_right)
                    else:
                        sheet.write(row, col, '{0:.2f}'.format(0).replace('.', ','), style_credit_note_right)
                else:
                    sheet.write(row, col, '{0:.2f}'.format(0).replace('.', ','), style_credit_note_right)
                row += 1
            total = p[2] + value_total
            sheet.write(row, col, '{0:.2f}'.format(total).replace('.', ','), style_ingreso_right)
            aux_new = row + 2
            aux_row = row + 2
            value_total_payment = 0
            sheet.write(row, 0, 'Ingreso Neto', style_ingreso_net)
            ingreso_list.append(total)
            sheet.write(row + 1, 0, 'Total Cobranza', style_cobranza_left)
            if j == 1:
                sql_period_invoice = """
                                    Select result.name, sum(result.credit) as credit from
                                    (SELECT ape.name, 
                                            ape.id,
                                            ape.date_start,
                                           CASE WHEN Extract(year FROM aml.date) = %s and Extract(month FROM aml.date) = %s 
                                           then sum(aml.credit)
                                           else 0
                                           end as credit
                                        FROM account_move am
                                        LEFT JOIN account_move_line aml ON (aml.nro_comp=am.ref)
                                        LEFT JOIN account_period ape ON (am.invoice_period_id=ape.id)
                                        INNER JOIN account_journal aj ON (aml.journal_id=aj.id)
                                        where am.company_id=%d and am.type='out_invoice' and am.state='posted'
                                        and ape.name <> '' and am.ref <> '' and aml.account_internal_type='receivable' 
                                        and aj.type<>'general' 
                                        group by ape.name, ape.id, ape.date_start, aml.date
                                        order by ape.date_start) 
                                        as result group by result.name, result.date_start order by result.date_start;	
                                                        """ % (p[0], p[1] if len(p[1]) == 2 else '0' + p[1], company_id)
            else:
                sql_period_invoice = """
                                                    Select sum(result.credit) as credit from
                                                    (SELECT ape.name, 
                                                            ape.id,
                                                            ape.date_start,
                                                           CASE WHEN Extract(year FROM aml.date) = %s and Extract(month FROM aml.date) = %s 
                                                           then sum(aml.credit)
                                                           else 0
                                                           end as credit
                                                        FROM account_move am
                                                        LEFT JOIN account_move_line aml ON (aml.nro_comp=am.ref)
                                                        LEFT JOIN account_period ape ON (am.invoice_period_id=ape.id)
                                                        INNER JOIN account_journal aj ON (aml.journal_id=aj.id)
                                                        where am.company_id=%d and am.type='out_invoice' and am.state='posted'
                                                        and ape.name <> '' and am.ref <> '' and aml.account_internal_type='receivable'
                                                        and aj.type <> 'general'
                                                        group by ape.name, ape.id, ape.date_start, aml.date
                                                        order by ape.date_start) 
                                                        as result group by result.name, result.date_start order by result.date_start;	
                                                                        """ % (
                    p[0], p[1] if len(p[1]) == 2 else '0' + p[1], company_id)

            self._cr.execute(sql_period_invoice)
            invoice_periods = self._cr.fetchall()
            for ip in invoice_periods:
                if j == 1:
                    sheet.write(aux_new, 0, ip[0], style_invoice_left)
                    sheet.write(aux_new, col, '{0:.2f}'.format(ip[1]).replace('.', ','), style_payment_right)
                    value_total_payment += ip[1]
                else:
                    sheet.write(aux_new, col, '{0:.2f}'.format(ip[0]).replace('.', ','), style_payment_right)
                    value_total_payment += ip[0]
                aux_new += 1
            j += 1
            payment_list.append(value_total_payment)
            sheet.write(aux_row - 1, col, '{0:.2f}'.format(value_total_payment).replace('.', ','), style_cobranza_right)
            sheet.write(aux_new, 0,
                        'EFICIENCIA DE COBRANZA [%]',
                        style_cobranza_left)
            if ingreso_list[col - 1] != 0:
                sheet.write(aux_new, col,
                            '{0:.2f}'.format((payment_list[col - 1] / ingreso_list[col - 1]) * 100).replace('.', ',') + '%',
                            style_cobranza_right)
            else:
                sheet.write(aux_new, col, 0.00, style_cobranza_right)
            col += 1
        return True

    def search_value_period_type(self, type, year, month, company_id):
        sql_value = """
            SELECT sum(am.amount_total_signed) as amount_total
                FROM account_move am	
                where am.company_id=%d and am.state='posted' and am.type='out_refund' 
                and Extract(year FROM invoice_date) = %s 
                and	Extract(month FROM invoice_date) = %s
                and am.internal_type_id = %d
           """ % (company_id, year, month if len(month) == 2 else '0' + month, type)
        self._cr.execute(sql_value)
        values = self._cr.fetchall()
        return values
