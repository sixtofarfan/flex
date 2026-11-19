# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class AccountBalancePeriodRep(models.TransientModel):
    _inherit = 'account.balance.period.rep'

    journal_id = fields.Many2one('account.journal', string='Diario')
    type_document_id = fields.Many2many('einvoice.catalog.01', 'period_rep_catalog_01_rel', string='Tipo de Documento')
    bills = fields.Selection([
        ('allow_bills', 'Agregar Letras'),
        ('only_bills', 'Solo Letras'),
    ], string='Letras')

    # is_not_home = fields.Boolean(string='No Domiciliado	')
    is_not_home = fields.Selection([
        ('dom', 'Domiciliados'),
        ('no_dom', 'No Domiciliados'),
    ], string='Tipo Cliente')
    bill_to_numberdocument = fields.Many2one(comodel_name='res.partner', string='Partner a Cobrar ')

    

    def get_report_gamma(self):
        sql_only_pending = ""
        if not self.only_pending:
            sql_type = 0
        else:
            sql_type = 1
            #sql_only_pending = "and (saldo_mn + saldo_me  != 0) and am.invoice_payment_state != 'paid'"
            #sql_only_pending = "and am.invoice_payment_state != 'paid'"
            sql_only_pending = "and (saldo_mn + saldo_me  != 0) "
        
        sql_type_account = """"""
        sql_partner = """"""
        sql_account = """"""
        sql_journal = """"""
        sql_type_document = """"""
        sql_bills = """"""
        sql_is_not_home = """ """
        sql_bill_to_numberdocument = """ """

        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if self.partner_id:
            sql_partner = """and a1.partner_id = %s""" % (self.partner_id.id)
        if self.account_id:
            sql_account = """and a1.account_id = %s""" % (self.account_id.id)
        if self.type_account:
            sql_type_account = """and a3.type = '%s'""" % (self.type_account)
        if self.journal_id:
            sql_journal = """and a1.journal_id = '%s'""" % (self.journal_id.id)
        if self.type_document_id:
            sql_type_document = """and a1.td_sunat in (%s)""" % (','.join(["'" + str(i) + "'" for i in self.type_document_id.mapped('code')]))
        if self.bills == 'allow_bills' or not MainParameter.bill_account_ids.ids:
            sql_bills = """"""
        elif self.bills == 'only_bills':
            sql_account = """"""
            sql_bills = """and a1.account_id in (%s)""" % (','.join(["'"+ str(i) + "'" for i in MainParameter.bill_account_ids.ids]))
        else:
            sql_bills = """and a1.account_id not in (%s)""" % (','.join(["'"+ str(i) + "'" for i in MainParameter.bill_account_ids.ids]))
        
        if self.is_not_home:
            sql_is_not_home = """and rp.is_not_home =  %s""" %  ('true' if self.is_not_home != 'dom' else 'false')
        
        if self.bill_to_numberdocument.id:
            sql_bill_to_numberdocument = """and am.bill_to_numberdocument = '%s'""" % (self.bill_to_numberdocument.id)    

        sql = """
DROP VIEW IF EXISTS account_balance_period_book_gamma;
CREATE OR REPLACE view account_balance_period_book_gamma as (
SELECT 
row_number() OVER () AS id,
a1.partner,
a1.fecha_doc,
a1.fecha_ven,
so.name as order_name,
a1.td_sunat,
a1.nro_comprobante,
case when rc.name is not null then 0 else a1.saldo_mn end as saldo_mn,
case when rc.name is not null then a1.saldo_me else 0 end as saldo_me,
case when rc.name is not null then rc.name else 'PEN' end as moneda,
apt.code as plazo,
so.client_order_ref as order_ref,
so.internal_ref_child as ref_hija,
so.foreign_agent_name as foreign_agent_name,
so.consignne_name as consignne_name,
so.client_order_ref as client_order_ref,
so.delivery_child_number as hbl,
rp.is_not_home as homeless,
case when fecha_ven >= CURRENT_DATE
then 'Por vencer'
else 'Vencido'
end as estado,
a1.aml_ids,
am.invoice_payment_state,
am.corporate_reference,
am.shipping_documents,
--aml.amount_currency as importe_total,
--aml.debit - aml.credit as  importe_total_pen
case when aml.amount_currency != 0 then aml.amount_currency else 0 end as importe_total,
case when aml.amount_currency = 0 then aml.debit - aml.credit else 0 end as importe_total_pen,
am.bill_to_numberdocument as partner_cobrar
FROM get_saldos('%s','%s',%s,%s) a1
LEFT JOIN res_partner rp on rp.id = a1.partner_id
LEFT JOIN account_account a2 ON a2.id = a1.account_id
LEFT JOIN account_account_type a3 ON a3.id = a2.user_type_id
LEFT JOIN account_move_line aml on aml.id = a1.move_line_id
LEFT JOIN account_move am on am.id = aml.move_id
LEFT JOIN res_currency rc on rc.id = aml.currency_id
LEFT JOIN sale_order so on so.id = aml.order_id
LEFT JOIN account_payment_term apt on apt.id = am.invoice_payment_term_id
WHERE a1.id is not null %s %s %s %s %s %s %s  %s %s and a1.libro != '79')""" % (
            self.date_ini.strftime('%Y/%m/%d'),
            self.date_end.strftime('%Y/%m/%d'),
            str(self.company_id.id),
            str(sql_type),
            sql_type_account,
            sql_partner,
            sql_account,
            sql_journal,
            sql_type_document,
            sql_bills,
            sql_only_pending,
            sql_is_not_home,
            sql_bill_to_numberdocument
            )

        self.env.cr.execute(sql)
        print(sql)
        if self.type_show == 'pantalla':
            return {
                'name': 'Saldo por Fecha Cont',
                'type': 'ir.actions.act_window',
                'res_model': 'account.balance.period.book.gamma',
                'view_mode': 'tree',
                'view_type': 'form',
                'views': [(False, 'tree')],
                'search_view_id': self.env.ref('fxo_account_balance_collection_gamma.search_account_balance_period_book_tree_gamma').id,
            }

        if self.type_show == 'excel':
            return self.get_excel()

        if self.type_show == 'pdf':
            return True

    def get_excel(self):
        import io
        from xlsxwriter.workbook import Workbook
        ReportBase = self.env['report.base']
        direccion = self.env['main.parameter'].search([('company_id','=',self.company_id.id)],limit=1).dir_create_file

        if not direccion:
            raise UserError(u'No existe un Directorio Exportadores configurado en Parametros Principales de Contabilidad para su Compañía')

        workbook = Workbook(direccion +'Saldo_por_Fecha_Doc.xlsx')
        workbook, formats = ReportBase.get_formats(workbook)

        import importlib
        import sys
        importlib.reload(sys)

        worksheet = workbook.add_worksheet("Saldo por Fecha Doc")
        worksheet.set_tab_color('blue')

        HEADERS = [
            'Partner',
            'Fecha de Emision',
            'Fecha de Vencimiento',
            'Numero de Operacion',
            'Tipo de Documento',
            'Nro. de Doc.',
            'Saldo Moneda Nacional',
            'Saldo Moneda Extranjera',
            'Moneda',
            'Plazo de Pago',
            'Referencia Hija',
            'Referencia Cliente',
            'HBL',
            'Agente del Exterior',
            'Consignatario',
            'Referencia del Cliente',
            'Ref. Corporativa',
            'Booking/BL',
            'Estado',
            'No Domiciliado',
            'Total USD',
            'Total S/'
        ]
        worksheet = ReportBase.get_headers(worksheet, HEADERS, 0, 0, formats['boldbord'])
        x=1
        #Totals#
        saldo_mn, saldo_me = 0, 0
        total_pen_por_vencer, total_pen_vencido, total_usd_por_vencer, total_usd_vencido = 0, 0, 0, 0

        for line in self.env['account.balance.period.book.gamma'].search([]):
            worksheet.write(x,0,line.partner if line.partner else '',formats['especial1'])
            worksheet.write(x,1,line.fecha_doc if line.fecha_doc else '',formats['dateformat'])
            worksheet.write(x,2,line.fecha_ven if line.fecha_ven else '',formats['dateformat'])
            worksheet.write(x,3,line.order_name if line.order_name else '',formats['especial1'])
            worksheet.write(x,4,line.td_sunat if line.td_sunat else '',formats['especial1'])
            worksheet.write(x,5,line.nro_comprobante if line.nro_comprobante else '',formats['especial1'])
            worksheet.write(x,6,line.saldo_mn if line.saldo_mn else 0,formats['numberdos'])
            worksheet.write(x,7,line.saldo_me if line.saldo_me else 0,formats['numberdos'])
            worksheet.write(x,8,line.moneda if line.moneda else '',formats['especial1'])
            worksheet.write(x,9,line.plazo if line.plazo else '',formats['especial1'])
            worksheet.write(x,10,line.ref_hija if line.ref_hija else '',formats['especial1'])
            worksheet.write(x,11,line.order_ref if line.order_ref else '',formats['especial1'])
            worksheet.write(x,12,line.hbl if line.hbl else '',formats['especial1'])

            worksheet.write(x,13,line.foreign_agent_name if line.foreign_agent_name else '',formats['especial1'])
            worksheet.write(x,14,line.consignne_name if line.consignne_name else '',formats['especial1'])
            worksheet.write(x,15,line.client_order_ref if line.client_order_ref else '',formats['especial1'])
            worksheet.write(x,16,line.corporate_reference if line.corporate_reference else '',formats['especial1'])
            worksheet.write(x,17,line.shipping_documents if line.shipping_documents else '',formats['especial1'])
            worksheet.write(x,18,line.estado if line.estado else '',formats['especial1'])
            worksheet.write(x,19,'No Domiciliado' if line.homeless else 'Domiciliado',formats['especial1'])
            worksheet.write(x,20,line.importe_total if line.importe_total else '',formats['numberdos'])
            worksheet.write(x,21,line.importe_total_pen if line.importe_total_pen else '',formats['numberdos'])


            x += 1
            saldo_mn += line.saldo_mn if line.saldo_mn else 0
            saldo_me += line.saldo_me if line.saldo_me else 0

            if line.estado == 'Por vencer' and line.moneda == 'PEN':
                total_pen_por_vencer += line.saldo_mn
            elif line.estado == 'Por vencer' and line.moneda == 'USD':
                total_usd_por_vencer += line.saldo_me
            elif line.estado == 'Vencido' and line.moneda == 'PEN':
                total_pen_vencido += line.saldo_mn
            elif line.estado == 'Vencido' and line.moneda == 'USD':
                total_usd_vencido += line.saldo_me

        worksheet.write(x,6,saldo_mn,formats['numbertotal'])
        worksheet.write(x,7,saldo_me,formats['numbertotal'])
        x += 2
        worksheet.write(x, 6, 'Total Soles Vencido', formats['boldbord'])
        worksheet.write(x, 7, total_pen_vencido, formats['numbertotal'])
        worksheet.write(x, 8, 'Total Soles Por vencer', formats['boldbord'])
        worksheet.write(x, 9, total_pen_por_vencer, formats['numbertotal'])
        x += 1
        worksheet.write(x, 6, 'Total Dolares Vencido', formats['boldbord'])
        worksheet.write(x, 7, total_usd_vencido, formats['numbertotal'])
        worksheet.write(x, 8, 'Total Dolares Por vencer', formats['boldbord'])
        worksheet.write(x, 9, total_usd_por_vencer, formats['numbertotal'])

        widths = [14] * 14
        worksheet = ReportBase.resize_cells(worksheet,widths)
        workbook.close()
        f = open(direccion + 'Saldo_por_Fecha_Doc.xlsx', 'rb')
        return self.env['popup.it'].get_file('Saldo por Fecha Documento Gamma.xlsx',base64.encodestring(b''.join(f.readlines())))