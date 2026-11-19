# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import *
import base64


class MultipaymentAdvanceWizard(models.TransientModel):
    _name = 'multipayment.advance.wizard'
    _description = 'Multipayment Advance Wizard'

    sunat_file = fields.Binary(string='Archivo Recibido')

    def import_sunat_txt(self):
        if not self.sunat_file:
            raise UserError('Es necesario especificar un archivo de importacion')
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        Multipayment = self.env['multipayment.advance.it'].browse(self._context.get('active_id'))
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        route = MainParameter.dir_create_file + 'Detracciones_Sunat.txt'
        tmp = open(route, 'wb+')
        tmp.write(base64.b64decode(self.sunat_file))
        tmp.close()
        parse_date = ''
        size = len(open(route).readlines())
        with open(route, encoding='cp1252') as f:
            log = ''
            for c, line in enumerate(f, 1):
                if c == 1:
                    continue
                elif len(line.split('|')) > 1:
                    Partner = self.env['res.partner'].search([('vat', '=', line.split('|')[7])], limit=1)
                    if not Partner:
                        log += 'No se encontro el partner con el nro documento %s en la linea %d\n' % (
                            line.split('|')[7], c)
                        continue
                    Catalog = self.env['einvoice.catalog.01'].search([('code', '=', line.split('|')[13])], limit=1)
                    if not Catalog:
                        log += 'No se encontro el tipo de documento con el codigo %s en la linea %d\n' % (
                            line.split('|')[13], c)
                        continue
                    serie = line.split('|')[14]
                    number = line.split('|')[15]
                    ref = serie + '-' + number
                    MoveLine = self.env['account.move.line'].search([
                        ('move_id.ref', '=', ref),
                        ('move_id.state', '=', 'posted'),
                        ('account_internal_type', 'in', ['receivable', 'payable']),
                        ('amount_residual', '!=', 0),
                        ('reconciled', '=', False),
                        ('type_document_id', '=', Catalog.id),
                        ('partner_id', '=', Partner.id),
                    ], limit=1)
                    if not MoveLine:
                        log += 'No se encontro el documento %s en la linea %d' % (ref, c)
                        continue
                    pay_line = self.env['multipayment.advance.it.line'].create({
                        'main_id': Multipayment.id,
                        'partner_id': Partner.id,
                        'tipo_documento': Catalog.id,
                        'invoice_id': MoveLine.id,
                    })
                    pay_line.on_change_invoice_id()
                    pay_line._get_partner_bank_account()

                    currency_name = MoveLine.move_id.currency_id.name
                    currency_rate = MoveLine.move_id.currency_rate
                    currency_rate = currency_rate if currency_rate > 0 else 1

                    importe_divisa = float(line.split('|')[10])
                    importe_divisa = -abs(importe_divisa / currency_rate) if currency_name == 'USD' else -abs(
                        importe_divisa)

                    pay_line.importe_divisa = importe_divisa
                    pay_line._update_debit_credit()
                    pay_line.main_id._get_line_ids()
            if log:
                return self.env['popup.it'].get_message(
                    'Ocurrieron los siguientes problemas, elimine las lineas que no han sido listadas aqui y vuelva a subir su archivo:\n' + log)
        Multipayment.write({'sunat_file_import': self.sunat_file})
        return self.env['popup.it'].get_message('Se Importo el archivo correctamente')
