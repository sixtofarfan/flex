# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

class AccountDetractionsWizard(models.TransientModel):
    _inherit = 'account.detractions.wizard'

    fecha = fields.Date(default=fields.Date.today())

    def get_data(self, invoice, m):
        return {
            'journal_id': m.detraction_journal.id,
            'ref': (invoice.ref if invoice.ref else 'Borrador'),
            'date': self.fecha,
            'invoice_date': invoice.invoice_date,
            'company_id': invoice.company_id.id,
            'glosa': 'PROVISION DE LA DETRACCION DE LA FACTURA ' + invoice.ref,
            'currency_rate': invoice.currency_rate,
            'type_op_det': invoice.type_op_det,
            'code_operation': invoice.code_operation,
            'partner_id': invoice.partner_id.id if invoice.partner_id else None,
        }

    def generar(self):
        log_info = ''
        invoice = self.env['account.move'].browse(self._context.get('active_id'))
        m = self.env['main.parameter'].search([('company_id', '=', invoice.company_id.id)], limit=1)

        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter.round_journal_id:
            raise UserError(
                'Falta configurar Diario de Redondeo en Parametros Principales/Asistentes/Diarios para Asistentes')
        if not m.detraction_journal.id:
            raise UserError(
                u"No esta configurada el Diario de Detracción en Parametros Principales de Contabilidad para su Compañía")

        if not invoice.type_op_det:
            raise UserError(u"Tipo de Operación Obligatorio al generar la detracción en el documento %s" % invoice.name)
        if not invoice.code_operation:
            raise UserError(
                u"Codigo de Operación Obligatorio al generar la detracción en el documento %s" % invoice.name)
        flag_ver = True
        data = self.get_data(invoice, m)
        if invoice.name_move_detraccion and invoice.diario_move_detraccion.id == m.detraction_journal.id and invoice.fecha_move_detraccion == invoice.invoice_date:
            data['name'] = invoice.name_move_detraccion
            flag_ver = False
        else:
            invoice.diario_move_detraccion = m.detraction_journal.id
            invoice.fecha_move_detraccion = invoice.invoice_date
            flag_ver = True
        lines = []
        doc = self.env['einvoice.catalog.01'].search([('code', '=', '00')], limit=1)
        filtered_line = invoice.line_ids.filtered(lambda l: l.account_id.internal_type in ['receivable', 'payable'])
        # SFR
        tc = invoice.currency_rate
        if invoice.currency_id.name == 'USD':
            currency_rate = self.env['res.currency.rate']
            rate = currency_rate.search([
                                ('currency_id', '=', invoice.currency_id.id),
                                ('name', '=', self.fecha),
                                ('company_id','=',invoice.company_id.id)
                            ], limit=1)
            if rate:
                tc = rate[0].sale_type
        
        if invoice.type == 'in_invoice':
            if not m.detractions_account.id:
                raise UserError(
                    u"No esta configurada la Cuenta de Detracción para Proveedor en Parametros Principales de Contabilidad para su Compañía")
            if invoice.currency_id.name == 'USD':
                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': float_round(self.monto * invoice.currency_rate,2),
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'currency_id': invoice.currency_id.id,
                    'amount_currency': self.monto,
                    'tc': invoice.currency_rate,
                    'company_id': invoice.company_id.id,
                    'date_maturity': self.fecha,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': m.detractions_account.id,
                    'debit': 0,
                    'credit': float_round(self.monto * invoice.currency_rate, 2),
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                    'date_maturity': self.fecha,
                    'tc': invoice.currency_rate,
               })
                lines.append(line_cc)
                # Si hay diferencia creamos la linea
                # La cuenta la obetenmos del modulo de letras de lo contrario conversar con Sixto
                difference = sum(line[2]['debit'] for line in lines) - sum(line[2]['credit'] for line in lines)
                difference = float_round(difference, 2)
                round_journal_id = MainParameter.round_journal_id
                account_id = round_journal_id.default_debit_account_id if difference < 0 else round_journal_id.default_credit_account_id
                if difference != 0:
                    line_cc = (0, 0, {
                        'account_id': account_id.id,
                        'debit': abs(difference) if difference < 0 else 0,
                        'credit': difference if difference > 0 else 0,
                        'name': _('Currency round difference'),
                        'partner_id': invoice.partner_id.id,
                        'nro_comp': invoice.ref,
                        'type_document_id': doc.id,
                        'company_id': invoice.company_id.id,
                    })
                    lines.append(line_cc)
            else:
                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': float_round(self.monto, 2),
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'company_id': invoice.company_id.id,
                    'date_maturity': self.fecha,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': m.detractions_account.id,
                    'debit': 0,
                    'credit': float_round(self.monto, 2),
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                    'date_maturity': self.fecha,
                })
                lines.append(line_cc)
        if invoice.type == 'out_invoice':
            if not m.customer_account_detractions.id:
                raise UserError(
                    u"No esta configurada la Cuenta de Detracción para Clientes en Parametros Principales de Contabilidad para su Compañía")
            if invoice.currency_id.name == 'USD':
                line_cc = (0, 0, {
                    'account_id': m.customer_account_detractions.id,
                    'debit': float_round(self.monto * invoice.currency_rate,2),
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': 0,
                    'credit': float_round(self.monto * invoice.currency_rate, 2),
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'currency_id': invoice.currency_id.id,
                    'amount_currency': abs(self.monto) * -1,
                    'tc': invoice.currency_rate,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)
                # Si hay diferencia creamos la linea
                # La cuenta la obetenmos del modulo de letras de lo contrario conversar con Sixto
                difference = sum(line[2]['debit'] for line in lines) - sum(line[2]['credit'] for line in lines)
                difference = float_round(difference,2)
                round_journal_id = MainParameter.round_journal_id
                account_id = round_journal_id.default_debit_account_id if difference < 0 else round_journal_id.default_credit_account_id
                if difference != 0:
                    line_cc = (0, 0, {
                        'account_id': account_id.id,
                        'debit': abs(difference) if difference < 0 else 0,
                        'credit': difference if difference > 0 else 0,
                        'name': _('Currency round difference'),
                        'partner_id': invoice.partner_id.id,
                        'nro_comp': invoice.ref,
                        'type_document_id': doc.id,
                        'company_id': invoice.company_id.id,
                    })
                    lines.append(line_cc)

            else:
                line_cc = (0, 0, {
                    'account_id': m.customer_account_detractions.id,
                    'debit': float_round(self.monto,2),
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': 0,
                    'credit': float_round(self.monto,2),
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

        data['line_ids'] = lines
        try:
            data["currency_rate"] = invoice.currency_rate
            tt = self.env['account.move'].create(data)
        except Exception as e:
            raise UserError(('Ocurrió el siguiente error al crear el asiento en la factura %s: ' + str(e)) % invoice.ref)

        ids_conciliation = []
        ids_conciliation.append(filtered_line.id)

        for line in tt.line_ids:
            if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
                ids_conciliation.append(line.id)

        if len(ids_conciliation) > 1:
            self.env['account.move.line'].browse(ids_conciliation).reconcile()

        if tt.state == 'draft':
            tt.post()
        invoice.move_detraccion_id = tt.id

        if not tt.invoice_date:
            tt.invoice_date = invoice.invoice_date
        if flag_ver:
            invoice.name_move_detraccion = tt.name

        return True
