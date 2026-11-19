# -*- coding: utf-8 -*-

from odoo import api, fields, models

class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    @api.model
    def process_bank_statement_line(self, st_line_ids, data):
        res = super(AccountReconciliation, self).process_bank_statement_line(st_line_ids, data)
        for move_id in res['moves']:
            am = self.env['account.move'].search([('id', '=', move_id)])
            st_line = self.env['account.bank.statement.line'].search([('id', 'in', st_line_ids)])
            aml_counterpart = False
            if data[0]['counterpart_aml_dicts']:
                aml_counterpart = self.env['account.move.line'].search([('id','=', data[0]['counterpart_aml_dicts'][0]['counterpart_aml_id'])])
            for aml in am.line_ids:
                if st_line.type_document_id:
                    aml.type_document_id = st_line.type_document_id
                else:
                    aml.type_document_id = self.env['einvoice.catalog.01'].search([('code','=','00')])
                if st_line.ref and (aml.nro_comp == '' or not aml.nro_comp):
                    aml.nro_comp = st_line.ref
                if aml_counterpart:
                    aml.move_id.invoice_date = aml_counterpart.move_id.invoice_date
                    aml.date_maturity = aml_counterpart.date_maturity
                else:
                    aml.move_id.invoice_date = st_line.date
                    aml.date_maturity = st_line.date
        return res
