# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import *
from odoo.exceptions import UserError
import base64

from io import BytesIO
import re
import uuid


class MassivePaymentDetractionsWizard(models.TransientModel):
    _inherit = 'massive.payment.detractions.wizard'

    def get_txt(self):
        # Changing source of code_operation and type_operation
        # Adding raise when any of this fields are missing
        ReportBase = self.env['report.base']
        lot_numer = self.multipayment_id.detraction_lot_number
        if not lot_numer:
            raise UserError(
                u'Es necesario llenar el campo Número de Lote de Detracciones en los Pagos Multiples Avanzados')
        ruc = self.multipayment_id.company_id.partner_id.vat

        if not ruc:
            raise UserError('No configuro el RUC de su Compañia.')

        # RUC + .tc
        name_doc = "D" + str(ruc) + lot_numer + ".txt"
        sum_total = 0
        if self.type == 'cp':
            for i in self.multipayment_id.invoice_ids:
                sum_total += i.debe
        else:
            for i in self.multipayment_id.invoice_ids:
                sum_total += i.haber
        ctxt = "*" + str(ruc) + self.get_text_with_size(self.multipayment_id.company_id.partner_id.name, 35, ' ',
                                                        True) + lot_numer + self.get_text_with_size(
            self.get_str_number(ReportBase.custom_round(sum_total)), 15, '0', False)
        ctxt += """\r\n"""
        for elem in self.multipayment_id.invoice_ids:
            ctxt += '6' + elem.partner_id.vat + self.get_text_with_size(None, 35, ' ', True) + '000000000'
            code_operation = elem.invoice_id.move_id.code_operation
            ctxt += self.get_text_with_size(code_operation, 3, '0', False)
            acc_bank = self.env['res.partner.bank'].search(
                [('partner_id', '=', elem.partner_id.id), ('is_detraction_account', '=', True)], limit=1)
            if self.type == 'cp' and acc_bank.acc_number:
                ctxt += self.get_text_with_size(acc_bank.acc_number, 11, ' ', False)
            elif self.type == 'cp' and not acc_bank.acc_number:
                ctxt += self.get_text_with_size(None, 11, ' ', False)
            else:
                ctxt += ''
            ctxt += self.get_text_with_size(self.get_str_number(ReportBase.custom_round(elem.debe)), 15, '0',
                                            False) if self.type == 'cp' else self.get_text_with_size(
                self.get_str_number(ReportBase.custom_round(elem.haber)), 15, '0', False)
            type_op_det = elem.invoice_id.move_id.type_op_det
            if not type_op_det:
                raise UserError(u'Debe definir el Tipo de Operación de Detracción en su Factura')
            ctxt += type_op_det
            Move = self.env['account.move'].search(
                [('type_document_id.code', '=', '01'), ('ref', '=', elem.invoice_id.move_id.ref)])
            if not Move:
                date = elem.invoice_id.move_id.invoice_date if elem.invoice_id.move_id.invoice_date else elem.invoice_id.move_id.date
            else:
                date = Move[0].invoice_date
            ctxt += str(date.year) + str('{:02d}'.format(date.month))
            ctxt += '01'
            partition = elem.invoice_id.nro_comp.split('-')
            if len(partition) == 2:
                ctxt += self.get_text_with_size(partition[0], 4, '0', False) + self.get_text_with_size(partition[1], 8,
                                                                                                       '0', False)
                ctxt += """\r\n"""
            if len(partition) == 1:
                ctxt += self.get_text_with_size(partition[0], 4, '0', False)
                ctxt += """\r\n"""
        import importlib
        import sys
        importlib.reload(sys)

        return self.env['popup.it'].get_file(name_doc, base64.encodestring(b'' + ctxt.encode("utf-8")))
