# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64


class MultipaymentAdvanceIt(models.Model):
    _inherit = 'multipayment.advance.it'

    is_retention_payment = fields.Boolean(string='Es pago de retenciones')
    is_supplier_payment = fields.Boolean(string='Es pago de proveedores')
    is_advance_payment = fields.Boolean(string='Es pago de anticipos')
    format_bank = fields.Selection(related='journal_id.bank_id.format_bank')
    provision_ids = fields.One2many('account.move.line', 'advance_id')
    advance_ids = fields.One2many('account.payment', 'advance_id')
    payment_method_id = fields.Many2one('account.payment.method', string='Metodo de Pago')
    batch_payment_id = fields.Many2one('account.batch.payment', string='Lote de Pago')
    detraction_file = fields.Binary(string='Archivo de Respuesta Detracciones')
    invoice_type = fields.Selection([
        ('out_invoice', 'Cobros'),
        ('in_invoice', 'Pagos')
    ], string='Tipo de Facturas', default='in_invoice')
    sunat_file_import = fields.Binary(string='Archivo Recibido Import Sunat')
    attachment_sunat_file_fname = fields.Char('Attachment Filename')
    date = fields.Date(string='Date', help="You can record the date of issue of any voucher")
    #date_maturity = fields.Date(string='Due Date', index=True,
    #    help="This field is used for payable and receivable journal entries. You can put the limit date for the payment of this line.")

    ####BBVA####
    process_type = fields.Selection([
        ('A', 'Inmediato'),
        ('H', 'Hora de Proceso'),
        ('F', 'Fecha Futura'),
    ], string='Tipo de Proceso', default='A')
    process_hour = fields.Selection([
        ('B', '11:00 a.m.'),
        ('C', '03:00 p.m.'),
        ('D', '07:00 p.m.'),
    ], string='Hora de Proceso')
    owner_validation = fields.Selection([
        ('S', 'Valida, si hay error rechaza el abono'),
        ('N', 'No valida'),
    ], string='Validacion de Pertenencia', default='S')
    alert_indicator = fields.Selection([
        ('E', 'Email'),
        ('C', 'Celular'),
    ], string='Indicador de Aviso', default='')

    ####BCP####
    flag = fields.Boolean(string='La cuenta de abono pertenece al titular de la cuenta origen', default=False)
    idc_flag = fields.Boolean(string='Desea validar IDC vs Cuenta', default=True)

    ####INTERBANK####
    company_code = fields.Char(string='Codigo de la Empresa', default='EE01')
    service_code = fields.Char(string='Codigo del Servicio', default='01')
    process_type_interbank = fields.Selection([
        ('0', 'En Linea'),
        ('1', 'En Diferido'),
    ], string='Tipo de Proceso', default='0')
    person_type = fields.Selection([
        ('P', 'Persona Natural'),
        ('C', 'Comercial o Juridica'),
    ], string='Tipo de Persona', default='C')
    detraction_type = fields.Selection([
        ('sc', 'Proveedor - Cliente'),
        ('cs', 'Cliente - Proveedor'),
    ], string='Tipo de Detraccion', default='sc')
    partner_cash_id = fields.Many2one(default=lambda self: self.get_partner_cash())

    def crear_asiento(self):
        if self.sunat_file_import and self.is_detraction_payment and self.invoice_type == 'out_invoice':
            log = ''
            for inv in self.invoice_ids:
                if inv.invoice_id.reconciled:
                    log += 'Ref: ' + inv.invoice_id.move_id.ref + '\n'
            if log:
                raise UserError('Los siguientes documentos ya han sido conciliados:\n' + log)
        res = super(MultipaymentAdvanceIt, self).crear_asiento()
        for line in self.asiento_id.line_ids:
            if line.account_id.code.startswith('10'):
                FirstLine = self.invoice_ids[0]
                Catalog = self.env['einvoice.catalog.01'].search([('code', '=', '00')])
                if not line.type_document_id:
                    line.type_document_id = Catalog.id
                #line.nro_comp = line.nro_comp if line.nro_comp else self.nro_operation
                if FirstLine:
                    line.partner_id = self.partner_cash_id  # FirstLine.partner_id.id

        self.asiento_id.currency_rate = self.tc
        self.asiento_id.invoice_date  = self.date if self.date else None
        # El asiento del pago lleva el tipo de factura de los documentos pagados
        # (si son de tipos distintos, el del primero, como el canje de letras)
        types = [t for t in self.invoice_ids.mapped('type_invoice') if t]
        if self.asiento_id and types:
            self.asiento_id.type_invoice = types[0]
        return res

    def _fx_partner_varios(self):
        """Socio VARIOS para cuando el detalle tiene documentos de varios socios."""
        Partner = self.env['res.partner']
        return Partner.search([('vat', '=', 'VARIOS')], limit=1) \
            or Partner.search([('name', '=', 'VARIOS')], order='id', limit=1)

    def _fx_partner_cash_target(self):
        self.ensure_one()
        partners = self.mapped('invoice_ids.partner_id.commercial_partner_id')
        if len(partners) == 1:
            return partners
        if len(partners) > 1:
            return self._fx_partner_varios() or self.partner_cash_id
        return self.partner_cash_id

    def _fx_set_partner_cash(self):
        """Partner Caja: el socio de los documentos si es uno solo; VARIOS si son
        varios. Se aplica al cambiar el detalle (no pisa un cambio manual
        posterior)."""
        for rec in self:
            target = rec._fx_partner_cash_target()
            if target and rec.partner_cash_id != target:
                rec.partner_cash_id = target.id

    # Antes este onchange se llamaba igual que el default (get_partner_cash) y
    # quedaba anulado por el: nunca se ejecutaba.
    @api.onchange('invoice_ids')
    def _onchange_invoice_ids_partner_cash(self):
        self._fx_set_partner_cash()

    @api.model
    def get_partner_cash(self):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        return MainParameter.partner_cash_id.id if MainParameter.partner_cash_id else None

    ####DETRACTIONS####
    def verify_detractions_fields(self):
        log = ''
        if not self.company_id:
            log += 'Necesita especificar una compañia\n'
        if not self.detraction_lot_number:
            log += 'Necesita especificar un numero de detraccion\n'
        if not self.detraction_type:
            log += 'Necesita especificar un tipo de detraccion\n'
        if not self.provision_ids:
            log += 'Necesita tener lineas de provision\n'
        for line in self.provision_ids:
            Invoice = self.env['account.move'].search([('move_detraccion_id', '=', line.move_id.id)])
            if not Invoice:
                log += 'La detraccion %s no esta asociada a ninguna factura\n' % line.move_id.name
            if not line.partner_id.vat:
                log += 'El partner %s no tiene un numero de documento asignado\n' % line.partner_id.name
            if not Invoice.type_good_service.code:
                log += 'El documento %s no tiene un codigo de bien o servicio\n' % Invoice.name
            if not Invoice.type_op_det:
                log += 'El documento %s no tiene un tipo de operacion\n' % Invoice.name
            if not Invoice.ref:
                log += 'El documento %s no tiene numero de comprobante\n' % Invoice.name
        if log:
            raise UserError('Se han detectado los siguientes errores\n' + log)

    def get_sunat_import(self):
        return {
            'name': 'Importacion',
            'type': 'ir.actions.act_window',
            'res_model': 'multipayment.advance.wizard',
            'views': [(self.env.ref('jp_automate_multipayment.view_multipayment_advance_wizard_import').id, 'form')],
            'context': self._context,
            'target': 'new',
        }

    def get_detractions_txt(self):
        self.verify_detractions_fields()
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        if not self.company_id.vat:
            raise UserError('No se ha definido un RUC para la compañia actual')
        Company = self.company_id
        doc_name = 'D{0}{1}.txt'.format(Company.vat, self.detraction_lot_number)
        route = MainParameter.dir_create_file + doc_name
        f = open(route, 'w+')
        f.write('*{vat}{name}{lot_number}{total}\r\n'.format(
            vat=self.parse_to_txt(Company.vat, 'str', range=11),
            name=self.parse_to_txt(Company.name, 'str', range=35),
            lot_number=self.parse_to_txt(self.detraction_lot_number, 'str', range=6),
            total=self.parse_to_txt(sum(self.provision_ids.mapped('debit')) if self.detraction_type == 'sp' \
                                        else sum(self.provision_ids.mapped('credit')), 'float', range=15, left=False),
        ))
        for line in self.provision_ids:
            PartnerAccount = line.partner_id.bank_ids.filtered(
                lambda l: len(l.acc_number) == 11 and l.type_of_account == '2')
            if not PartnerAccount:
                raise UserError('El partner %s no tiene una cuenta corriente de 11 digitos' % line.partner_id.name)
            date = line.move_id.invoice_date if line.move_id.invoice_date else line.move_id.date
            Invoice = self.env['account.move'].search([('move_detraccion_id', '=', line.move_id.id)])
            f.write(
                '6{p_doc_num}{p_name}{proform}{code}{p_account}{amount}{op_code}{period}{type}{serie}{number}\r\n'.format(
                    p_doc_num=self.parse_to_txt(line.partner_id.vat, 'str', range=11),
                    p_name=' ' * 35,
                    proform='0' * 9,
                    code=self.parse_to_txt(Invoice.type_good_service.code, 'str', range=3),
                    p_account=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=11),
                    amount=self.parse_to_txt(line.debit if self.detraction_type == 'sp' else line.credit, 'float',
                                             range=15, left=False),
                    op_code=self.parse_to_txt(Invoice.type_op_det, 'str', range=2),
                    period=str(date.year) + str('{:02d}'.format(date.month)),
                    type='01',
                    serie=self.parse_to_txt(Invoice.ref.split('-')[0], 'str', range=4),
                    number=self.parse_to_txt(Invoice.ref.split('-')[1], 'str', range=8),
                ))
        f.close()
        f = open(route, 'rb')
        return self.env['popup.it'].get_file(doc_name, base64.encodestring(b''.join(f.readlines())))

    def set_detraction_txt_data(self):
        if not self.detraction_file:
            raise UserError('No se ha especificado un Archivo de Respuesta de Detracciones')
        return self.env['get.invoices.wizard'].importing_file(self.detraction_file,
                                                              self.invoice_ids.mapped('invoice_id.move_id'))

    def get_invoices(self):
        if self.is_detraction_payment:
            return self.env['get.invoices.wizard'] \
                .with_context(active_ids=self.ids, active_model='multipayment.advance.it', active_id=self.id) \
                .get_invoices_detraction_wizard()
        else:
            return self.env['get.invoices.wizard'] \
                .with_context(active_ids=self.ids, active_model='multipayment.advance.it', active_id=self.id) \
                .get_invoices_wizard()

    def get_detractions(self):
        return self.env['get.invoices.wizard'] \
            .with_context(active_ids=self.ids, active_model='multipayment.advance.it', active_id=self.id) \
            .get_detractions_wizard()

    def get_provisions_wizard(self):
        return {
            'name': _('Provisions'),
            'type': 'ir.actions.act_window',
            'res_model': 'get.invoices.wizard',
            'views': [(self.env.ref('jp_automate_multipayment.view_get_provisions_wizard').id, 'form')],
            'context': self._context,
            'target': 'new',
        }

    def get_advances_wizard(self):
        return {
            'name': _('Advances'),
            'type': 'ir.actions.act_window',
            'res_model': 'get.invoices.wizard',
            'views': [(self.env.ref('jp_automate_multipayment.view_get_advances_wizard').id, 'form')],
            'context': self._context,
            'target': 'new',
        }

    def generate_detraction_lot(self):
        Batch = self.env['account.batch.payment'].create({
            'batch_type': 'outbound',
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'name': self.detraction_lot_number,
            'catalog_payment_id': self.catalog_payment_id.id,
            'state': 'draft',
        })
        lines = []
        for line in self.provision_ids:
            new_line = self.env['account.payment'].create({
                'partner_type': 'supplier' if line.partner_id.is_supplier else 'customer',
                'partner_id': line.partner_id.id,
                'amount': line.debit if line.debit > 0 else line.credit,
                'currency_id': line.move_id.currency_id.id,
                'payment_date': self.payment_date,
                'communication': self.glosa,
                'payment_type': 'outbound',
                'payment_method_id': self.payment_method_id.id,
                'journal_id': self.journal_id.id,
                'state': 'posted',
                'manual_batch_payment_id': Batch.id,
            })
            lines.append(new_line.id)
        Batch.payment_ids = [(6, 0, lines)]
        Batch.validate_batch()
        self.batch_payment_id = Batch.id
        self.state = 'done'
        return self.env['popup.it'].get_message('Se genero el Lote correctamente')

    def parse_to_txt(self, var, type, range=1, left=True, decimal_point=False):
        '''Parse the type of data int, str, float, date or datetime to txt format
        :param var: The variable that you wan't to parse
        :param type: The type of the var that you are using
        :param range: The space that are going to refill with the text
        :param left: The direction of the space that you are using, if you send False the space will turn to right
        :param decimal_point: The decimal point of the float var will be print in the txt
        :return: The plain text for the txt file
        '''
        if type not in ['date', 'datetime'] and len(str(var)) > range:
            var = str(var)[0:range]
        spacer = ' ' if type == 'str' else '0'
        aux = spacer * range
        if type in ['int', 'str']:
            var = str(var)
            var = var.replace('ñ', 'n')
            var = var.replace('Ñ', 'N')
            if left:
                res = var + aux[len(var):]
            else:
                res = aux[:-len(var)] + var
        elif type == 'float':
            var = self.env['report.base'].custom_round(var, 2)
            Lang = self.env['res.lang'].search([('active', '=', True)], limit=1)
            var = str(var).split(Lang.decimal_point)
            dp = Lang.decimal_point if decimal_point else ''
            if len(var[1]) == 1:
                var[1] += '0'
            if left:
                res = var[0] + dp + var[1] + aux[len(var[0] + dp + var[1]):]
            else:
                res = aux[:-len(var[0] + dp + var[1])] + var[0] + dp + var[1]
        elif type == 'date':
            aux = '00'
            year, month, day = str(var.year), str(var.month), str(var.day)
            res = year + aux[:-len(month)] + month + aux[:-len(day)] + day
        elif type == 'datetime':
            import pytz
            aux = '00'
            if not self.env.user.partner_id.tz:
                raise UserError(
                    'Es necesario que configure la zona horaria en el partner del usuario que esta utilizando')
            tz = pytz.timezone(self.env.user.partner_id.tz)
            date_tz = pytz.utc.localize(var).astimezone(tz)
            year, month, day = str(date_tz.year), str(date_tz.month), str(date_tz.day)
            hour, minute, second = str(date_tz.hour), str(date_tz.minute), str(date_tz.second)
            res = year + aux[:-len(month)] + month + aux[:-len(day)] + day + \
                  aux[:-len(hour)] + hour + aux[:-len(minute)] + minute + aux[:-len(second)] + second
        return res

    def get_acc(self, Partner, Journal, is_detraction=False):
        if is_detraction:
            PartnerAccount = Partner.bank_ids.filtered(lambda acc: acc.type_of_account == '2')
        else:
            PartnerAccount = Partner.bank_ids.filtered(lambda acc:
                                                       acc.bank_id == Journal.bank_id and \
                                                       acc.type_of_account in ['0', '1'] and \
                                                       acc.currency_id == Journal.bank_account_id.currency_id
                                                       )
            print('*********1',PartnerAccount)
            if not PartnerAccount:
                PartnerAccount = Partner.bank_ids.filtered(lambda acc:
                                                           acc.type_of_account == '3' and \
                                                           acc.currency_id == Journal.bank_account_id.currency_id
                                                           )
                print('*********2',PartnerAccount)
        if not PartnerAccount:
            return None
        else:
            return PartnerAccount[0]

    def check_account_type(self, BankAccount, bank):
        log = ''
        if not BankAccount.currency_id:
            log += 'No se ha especificado una moneda en la cuenta %s\n' % BankAccount.acc_number
        elif not BankAccount.type_of_account:
            log += 'No se ha especificado un tipo de cuenta en la cuenta %s\n' % BankAccount.acc_number
        elif BankAccount.type_of_account and BankAccount.type_of_account not in ['0', '1', '3']:
            log += 'La cuenta %s tiene un tipo de cuenta diferente a Corriente, Ahorros o Interbancaria\n' % BankAccount.acc_number

        if BankAccount.type_of_account == '3' and len(BankAccount.acc_number) != 20:
            log += 'La cuenta %s debe tener 20 digitos\n' % BankAccount.acc_number

        if bank == 'bbva':
            if BankAccount.branch_name:
                account = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
            else:
                account = BankAccount.acc_number
            if BankAccount.type_of_account in ['0', '1'] and len(account) != 20:
                log += 'La cuenta %s debe tener 20 digitos\n' % BankAccount.acc_number
        elif bank == 'bcp':
            if BankAccount.type_of_account == '0' and len(BankAccount.acc_number) != 13:
                log += 'La cuenta %s debe tener 13 digitos\n' % BankAccount.acc_number
            if BankAccount.type_of_account == '1' and len(BankAccount.acc_number) != 14:
                log += 'La cuenta %s debe tener 14 digitos\n' % BankAccount.acc_number
        elif bank == 'interbank':
            if BankAccount.type_of_account in ['0', '1'] and len(BankAccount.acc_number) != 13:
                log += 'La cuenta %s debe tener 13 digitos\n' % BankAccount.acc_number
        elif bank == 'scotiabank':
            if BankAccount.type_of_account in ['0', '1'] and len(BankAccount.acc_number) > 14:
                log += 'La cuenta %s debe tener menos de 14 digitos\n' % BankAccount.acc_number
        return log

    def get_txt(self):
        if not self.journal_id.bank_account_id:
            raise UserError('El diario seleccionado no tiene una cuenta bancaria definida')
        if self.format_bank == 'bbva':
            lines = self.get_lines(self.format_bank)
            self.verify_bbva_fields(lines)
            return self.get_bbva_txt(lines)
        elif self.format_bank == 'bcp':
            lines = self.get_lines(self.format_bank)
            self.verify_bcp_fields(lines)
            return self.get_bcp_txt(lines)
        elif self.format_bank == 'interbank':
            lines = self.get_lines(self.format_bank)
            self.verify_interbank_fields(lines)
            return self.get_interbank_txt(lines)
        elif self.format_bank == 'scotiabank':
            lines = self.get_lines(self.format_bank)
            self.verify_scotiabank_fields(lines)
            return self.get_scotiabank_txt(lines)
        else:
            raise UserError('El diario no tiene un banco con formato definido')

    def get_advance_txt(self):
        if not self.journal_id.bank_account_id:
            raise UserError('El diario seleccionado no tiene una cuenta bancaria definida')
        if self.format_bank == 'bbva':
            lines = self.get_lines_advance(self.format_bank)
            self.verify_bbva_fields(lines)
            return self.get_bbva_txt(lines)
        elif self.format_bank == 'bcp':
            lines = self.get_lines_advance(self.format_bank)
            self.verify_bcp_fields(lines)
            return self.get_bcp_txt(lines)
        elif self.format_bank == 'interbank':
            lines = self.get_lines_advance(self.format_bank)
            self.verify_interbank_fields(lines)
            return self.get_interbank_txt(lines)
        elif self.format_bank == 'scotiabank':
            lines = self.get_lines_advance(self.format_bank)
            self.verify_scotiabank_fields(lines)
            return self.get_scotiabank_txt(lines)
        else:
            raise UserError('El diario no tiene un banco con formato definido')

    def verify_bbva_fields(self, lines):
        log = ''
        BankAccount = self.journal_id.bank_account_id
        log += self.check_account_type(BankAccount, 'bbva')
        if BankAccount.type_of_account == '3':
            log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
        if not self.process_type:
            log += 'Necesita especificar un tipo de proceso\n'
        for line in lines:
            if not line.get('partner_id').l10n_latam_identification_type_id.bbva_code:
                log += 'El tipo de documento del partner %s no tiene su codigo BBVA\n' % line.get('partner_id').name
            if not line.get('partner_id').vat:
                log += 'El partner %s no tiene un numero de documento asignado\n' % line.get('partner_id').name
            PartnerAccount = line.get('partner_bank_acc_id')
            log += self.check_account_type(PartnerAccount, 'bbva')
            if not line.get('bank_code'):
                log += 'El tipo de documento %s no tiene su codigo BBVA\n' % line.get('tipo_documento')
            if not line.get('reference'):
                log += 'El documento %s no tiene numero de comprobante\n' % line.get('invoice_name')
        if log:
            raise UserError('Se han detectado los siguientes errores\n' + log)

    def verify_bcp_fields(self, lines):
        log = ''
        BankAccount = self.journal_id.bank_account_id
        log += self.check_account_type(BankAccount, 'bcp')
        if BankAccount.type_of_account == '3':
            log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
        for line in lines:
            if not line.get('partner_id').l10n_latam_identification_type_id.bcp_code:
                log += 'El tipo de documento del partner %s no tiene su codigo BCP\n' % line.get('partner_id').name
            if not line.get('partner_id').vat:
                log += 'El partner %s no tiene un numero de documento asignado\n' % line.get('partner_id').name
            PartnerAccount = line.get('partner_bank_acc_id')
            log += self.check_account_type(PartnerAccount, 'bcp')
            if not line.get('bank_code'):
                log += 'El tipo de documento %s no tiene su codigo BCP\n' % line.get('tipo_documento')
            if not line.get('reference'):
                log += 'El documento %s no tiene numero de comprobante\n' % line.get('invoice_name')
        if log:
            raise UserError('Se han detectado los siguientes errores\n' + log)

    def verify_interbank_fields(self, lines):
        log = ''
        BankAccount = self.journal_id.bank_account_id
        log += self.check_account_type(BankAccount, 'interbank')
        if BankAccount.type_of_account == '3':
            log += 'No se puede utilizar la cuenta %s de tipo interbancaria como cuenta de cargo\n' % BankAccount.acc_number
        if not self.company_code:
            log += 'El codigo de compañia es un campo obligatorio\n'
        if not self.service_code:
            log += 'El codigo de servicio es un campo obligatorio\n'
        if not self.process_type_interbank:
            log += 'El tipo de proceso es un campo obligatorio\n'
        if not self.person_type:
            log += 'El tipo de persona es un campo obligatorio\n'
        for line in lines:
            if not line.get('partner_id').l10n_latam_identification_type_id.interbank_code:
                log += 'El tipo de documento del partner %s no tiene su codigo Interbank\n' % line.get(
                    'partner_id').name
            if not line.get('partner_id').vat:
                log += 'El partner %s no tiene un numero de documento asignado\n' % line.get('partner_id').name
            if not line.get('bank_code'):
                log += 'El tipo de documento %s no tiene su codigo Interbank\n' % line.get('tipo_documento')
            PartnerAccount = line.get('partner_bank_acc_id')
            log += self.check_account_type(PartnerAccount, 'interbank')
            if not line.get('reference'):
                log += 'El documento %s no tiene numero de comprobante\n' % line.get('invoice_name')
        if log:
            raise UserError('Se han detectado los siguientes errores\n' + log)

    def verify_scotiabank_fields(self, lines):
        log = ''
        BankAccount = self.journal_id.bank_account_id
        log += self.check_account_type(BankAccount, 'scotiabank')
        for line in lines:
            if not line.get('partner_id').vat:
                log += 'El partner %s no tiene un numero de documento asignado\n' % line.get('partner_id').name
            PartnerAccount = line.get('partner_bank_acc_id')
            log += self.check_account_type(PartnerAccount, 'scotiabank')

    def get_lines(self, bank):
        lines = []
        for inv in self.invoice_ids:
            line = {}
            if not inv.partner_bank_acc_id:
                raise UserError('El partner %s no tiene una cuenta bancaria' % inv.partner_id.name)
            if bank == 'bbva':
                line['bank_code'] = inv.tipo_documento.bbva_code
            elif bank == 'bcp':
                line['bank_code'] = inv.tipo_documento.bbva_code
            elif bank == 'interbank':
                line['bank_code'] = inv.tipo_documento.interbank_code
            else:
                line['bank_code'] = ''
            line['partner_id'] = inv.partner_id
            line['partner_bank_acc_id'] = inv.partner_bank_acc_id
            line['debe'] = inv.debe
            line['haber'] = inv.haber
            line['tipo_documento'] = inv.tipo_documento.name
            line['invoice_name'] = inv.invoice_id.name
            line['doc_number'] = inv.invoice_id.move_id.ref
            line['reference'] = inv.invoice_id.move_id.name
            lines.append(line)
        return lines

    def get_lines_advance(self, bank):
        lines = []
        for adv in self.advance_ids:
            line = {}
            if not adv.partner_bank_acc_id:
                raise UserError('El partner %s no tiene una cuenta bancaria' % adv.partner_id.name)
            if bank == 'bbva':
                line['bank_code'] = 'F'
            elif bank == 'bcp':
                line['bank_code'] = 'F'
            elif bank == 'interbank':
                line['bank_code'] = 'F'
            else:
                line['bank_code'] = ''
            line['partner_id'] = adv.partner_id
            line['partner_bank_acc_id'] = adv.partner_bank_acc_id
            line['debe'] = adv.amount
            line['haber'] = 0
            line['tipo_documento'] = ''
            line['invoice_name'] = ''
            line['doc_number'] = adv.order_id.name
            line['reference'] = adv.cash_nro_comp
            lines.append(line)
        return lines

    def get_amounts_total(self, lines):
        amounts = []
        for line in lines:
            amounts.append(self.env['report.base'].custom_round(line.get('debe') + line.get('haber'), 2))
        return sum(amounts)

    def get_bbva_txt(self, lines):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        doc_name = '%sBBVA.txt' % MainParameter.dir_create_file
        f = open(doc_name, 'w+')
        BankAccount = self.journal_id.bank_account_id
        Bank = self.journal_id.bank_id
        total = self.get_amounts_total(lines)
        if not BankAccount.branch_name:
            raise UserError('No se ha especificado una sucursal en el banco')
        acc_number = BankAccount.acc_number[:8] + BankAccount.branch_name + BankAccount.acc_number[8:]
        parse_acc = self.parse_to_txt(BankAccount.acc_number, 'str', range=18)
        f.write(
            '750{account}{currency}{total}{process}{date}{hour}{reference}{total_lines}{valid}{ceros}{spaces}\n'.format(
                account=acc_number,
                currency=BankAccount.currency_id.name,
                total=self.parse_to_txt(total, 'float', range=15, left=False),
                process=self.process_type,
                date=self.parse_to_txt(self.payment_date, 'date') if self.process_type == 'F' else ' ' * 8,
                hour=self.process_hour if self.process_type == 'H' else ' ',
                reference=self.parse_to_txt(self.glosa, 'str', range=25) if self.glosa else ' ' * 25,
                total_lines=self.parse_to_txt(len(lines), 'int', range=6, left=False),
                valid=self.owner_validation,
                ceros='0' * 18,
                spaces=' ' * 50
            ))
        texts = []
        for line in lines:
            PartnerAccount = line.get('partner_bank_acc_id')
            if self.alert_indicator == 'E':
                alert_val = line.get('partner_id').email if line.get('partner_id').email else ''
            elif self.alert_indicator == 'C':
                alert_val = line.get('partner_id').phone if line.get('partner_id').phone else ''
            else:
                alert_val = ''
            text = '002{p_doc_type}{p_doc_num}{charge_type}{payment_doc}{beneficiary_name}{amount}{doc_type}{doc_number}{group_payment}{reference}{alert_indicator}{alert_val}{contact_user}{ceros}{spaces}'.format(
                p_doc_type=line.get('partner_id').l10n_latam_identification_type_id.bbva_code,
                p_doc_num=self.parse_to_txt(line.get('partner_id').vat, 'str', range=12),
                charge_type='I' if PartnerAccount.type_of_account == '3' else 'P',
                payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
                beneficiary_name=self.parse_to_txt(line.get('partner_id').name, 'str', range=40),
                amount=self.parse_to_txt(line.get('debe') if line.get('debe') else line.get('haber'), 'float', range=15,
                                         left=False),
                doc_type=line.get('bank_code'),
                doc_number=self.parse_to_txt(line.get('doc_number').replace('-', ''), 'str', range=12),
                group_payment='N',
                reference=self.parse_to_txt(line.get('reference'), 'str', range=40),
                alert_indicator=self.alert_indicator if self.alert_indicator else ' ',
                alert_val=self.parse_to_txt(alert_val, 'str', range=50),
                contact_user=' ' * 30,
                ceros='0' * 32,
                spaces=' ' * 18,
            )
            texts.append(text)
        f.write('\n'.join(texts))
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('BBVA.txt', base64.encodestring(b''.join(f.readlines())))

    def get_bcp_txt(self, lines):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        doc_name = '%sBCP.txt' % MainParameter.dir_create_file
        f = open(doc_name, 'w+')
        BankAccount = self.journal_id.bank_account_id
        Bank = self.journal_id.bank_id
        total = self.get_amounts_total(lines)
        ACCOUNT_TYPE = {'0': 'C', '1': 'A', '3': 'B'}

        acc_numbers = []
        for i in lines:
            PartnerAccount = i.get('partner_bank_acc_id')
            if PartnerAccount.type_of_account == '3':
                acc_numbers.append(int(PartnerAccount.acc_number[10:]))
            else:
                acc_numbers.append(int(PartnerAccount.acc_number[3:]))
        acc_numbers.append(int(BankAccount.acc_number[3:]))
        check_sum = sum(acc_numbers)
        f.write('1{total_lines}{date}{charge_type}{currency}{account}{total}{reference}{flag}{check_sum}\r\n'.format(
            total_lines=self.parse_to_txt(len(lines), 'int', range=6, left=False),
            date=self.parse_to_txt(self.payment_date, 'date'),
            charge_type='C',
            currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
            account=self.parse_to_txt(BankAccount.acc_number, 'str', range=20),
            total=self.parse_to_txt(total, 'float', range=17, left=False, decimal_point=True),
            reference=self.parse_to_txt(self.glosa, 'str', range=40),
            flag='S' if self.flag else 'N',
            check_sum=self.parse_to_txt(str(check_sum), 'str', range=15),
        ))
        for line in lines:
            PartnerAccount = line.get('partner_bank_acc_id')
            f.write('2{account_type}{payment_doc}{payment_type}{p_doc_type}{p_doc_num}   {beneficiary_name}\
{beneficiary_ref}{company_ref}{currency}{amount}{flag}\r\n'.format(
                account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' '),
                payment_doc=self.parse_to_txt(PartnerAccount.acc_number, 'str', range=20),
                payment_type='1',
                p_doc_type=line.get('partner_id').l10n_latam_identification_type_id.bcp_code,
                p_doc_num=self.parse_to_txt(line.get('partner_id').vat, 'str', range=12),
                beneficiary_name=self.parse_to_txt(line.get('partner_id').name, 'str', range=75),
                beneficiary_ref=self.parse_to_txt(line.get('reference').replace('-', ''), 'str', range=40),
                company_ref=self.parse_to_txt(self.env.company.name, 'str', range=20),
                currency='0001' if BankAccount.currency_id.name == 'PEN' else '1001',
                amount=self.parse_to_txt(line.get('debe') if line.get('debe') else line.get('haber'), 'float', range=17,
                                         left=False, decimal_point=True),
                flag='S' if self.idc_flag else 'N',
            ))
            f.write('3{doc_type}{doc_number}{amount}\r\n'.format(
                doc_type=line.get('bank_code'),
                doc_number=self.parse_to_txt(line.get('doc_number').replace('-', ''), 'str', range=12).zfill(15),
               amount=self.parse_to_txt(line.get('debe') if line.get('debe') else line.get('haber'), 'float', range=17,
                                         left=False, decimal_point=True),
            ))
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('BCP.txt', base64.encodestring(b''.join(f.readlines())))

    def get_interbank_txt(self, lines):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        doc_name = '%sInterbank.txt' % MainParameter.dir_create_file
        f = open(doc_name, 'w+')
        BankAccount = self.journal_id.bank_account_id
        Bank = self.journal_id.bank_id
        total = self.get_amounts_total(lines)
        after_date = fields.Date.today() if self.process_type_interbank == '0' else self.payment_date
        f.write('0103{company}{service}{account}{type_account}{currency}{reference}{date}{process_type}\
{after_date}{lines}{soles_total}{usd_total}MC001\r\n'.format(
            company=self.parse_to_txt(self.company_code, 'str', range=4),
            service=self.parse_to_txt(self.service_code, 'str', range=2),
            account=self.parse_to_txt(BankAccount.acc_number, 'str', range=13),
            type_account='001' if BankAccount.type_of_account == '0' else '002',
            currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
            reference=self.parse_to_txt(self.glosa, 'str', range=12),
            date=self.parse_to_txt(fields.Datetime.now(), 'datetime'),
            process_type=self.process_type_interbank,
            after_date=self.parse_to_txt(after_date, 'date'),
            lines=self.parse_to_txt(len(lines), 'int', range=6, left=False),
            soles_total=self.parse_to_txt(total, 'float', range=15,
                                          left=False) if BankAccount.currency_id.name == 'PEN' else '0' * 15,
            usd_total=self.parse_to_txt(total, 'float', range=15,
                                        left=False) if BankAccount.currency_id.name == 'USD' else '0' * 15,
        ))
        for line in lines:
            PartnerAccount = line.get('partner_bank_acc_id')
            ACCOUNT_TYPE = {'0': '001', '1': '002', '3': ' ' * 3}
            if self.person_type == 'P':
                benef_name = self.parse_to_txt(line.get('partner_id').name_p or '', 'str', range=20) + \
                             self.parse_to_txt(line.get('partner_id').last_name or '', 'str', range=20) + \
                             self.parse_to_txt(line.get('partner_id').m_last_name or '', 'str', range=20)
            else:
                benef_name = self.parse_to_txt(line.get('partner_id').name, 'str', range=60)
            f.write('02{benef_code}{doc_type}{doc_number}{date_to}{charge_currency}{amount} {charge_type}{account_type}\
{account_currency}{account_office}{acc_number}{person_type}{p_doc_type}{p_doc_num}{benef_name}{currency_cts}{amount_cts}\
{filler}{cell_phone}{email}\r\n'.format(
                benef_code=self.parse_to_txt(line.get('partner_id').vat, 'str', range=20),
                doc_type=line.get('bank_code'),
                doc_number=self.parse_to_txt(line.get('reference').replace('-', ''), 'str', range=20),
                date_to=' ' * 8,
                charge_currency='01' if BankAccount.currency_id.name == 'PEN' else '10',
                amount=self.parse_to_txt(line.get('debe') if line.get('debe') else line.get('haber'), 'float', 15,
                                         left=False),
                charge_type='99' if PartnerAccount.type_of_account == '3' else '09',
                account_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' ' * 3),
                account_currency=' ' * 2 if PartnerAccount.type_of_account == '3' else (
                '01' if BankAccount.currency_id.name == 'PEN' else '10'),
                account_office=' ' * 3 if PartnerAccount.type_of_account == '3' else PartnerAccount.acc_number[:3],
                acc_number=PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' \
                    else self.parse_to_txt(PartnerAccount.acc_number[:3], 'str', range=20),
                person_type=self.person_type if self.person_type else ' ',
                p_doc_type=line.get('partner_id').l10n_latam_identification_type_id.interbank_code,
                p_doc_num=self.parse_to_txt(line.get('partner_id').vat, 'str', range=15),
                benef_name=benef_name,
                currency_cts=' ' * 2,
                amount_cts=' ' * 15,
                filler=' ' * 6,
                cell_phone=self.parse_to_txt(line.get('partner_id').phone or '', 'str', range=40),
                email=self.parse_to_txt(line.get('partner_id').email or '', 'str', range=140),
            ))
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('Interbank.txt', base64.encodestring(b''.join(f.readlines())))

    def get_scotiabank_txt(self, lines):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter or not MainParameter.dir_create_file:
            raise UserError(
                u'No existe un Directorio de Descarga configurado en Parametros Principales para su Compañía')
        doc_name = '%sScotiabank.txt' % MainParameter.dir_create_file
        f = open(doc_name, 'w+')
        BankAccount = self.journal_id.bank_account_id
        Bank = self.journal_id.bank_id
        total = self.get_amounts_total(lines)
        ACCOUNT_TYPE = {'0': '2', '1': '3', '3': ' '}
        for line in lines:
            PartnerAccount = line.get('partner_bank_acc_id')
            f.write(
                '{doc_number}{beneficiary_name}{email}{p_doc_num} {charge_currency}{amount}{payment_type}{acc_number}{inter_acc_number}\r\n'.format(
                    doc_number=self.parse_to_txt(line.get('partner_id').vat, 'str', range=11),
                    beneficiary_name=self.parse_to_txt(line.get('partner_id').name, 'str', range=60),
                    email=self.parse_to_txt(line.get('partner_id').email or '', 'str', range=60),
                    p_doc_num=self.parse_to_txt(line.get('reference').replace('-', ''), 'str', range=18),
                    charge_currency='0' if BankAccount.currency_id.name == 'PEN' else '1',
                    amount=self.parse_to_txt(total, 'float', 17, left=False),
                    payment_type=ACCOUNT_TYPE.get(PartnerAccount.type_of_account, ' '),
                    acc_number=self.parse_to_txt(
                        PartnerAccount.acc_number if PartnerAccount.type_of_account in ['0', '1'] else '', 'str',
                        range=14),
                    inter_acc_number=self.parse_to_txt(
                        PartnerAccount.acc_number if PartnerAccount.type_of_account == '3' else '', 'str', range=20),
                ))
        f.close()
        f = open(doc_name, 'rb')
        return self.env['popup.it'].get_file('Scotiabank.txt', base64.encodestring(b''.join(f.readlines())))

    def _fx_invoice_totals(self):
        """Debe, Haber e Importe Divisa de las facturas/letras. Si el Debe/Haber
        de una linea todavia no se calculo, se deduce de su Importe Divisa (en
        pagos va al Debe, en cobros al Haber), asi la caja nunca sale del lado
        equivocado."""
        debe = haber = imp = 0.0
        foreign = bool(self.journal_id.currency_id) and self.journal_id.currency_id != self.company_id.currency_id
        for line in self.invoice_ids:
            imp += line.importe_divisa
            if line.debe or line.haber:
                debe += line.debe
                haber += line.haber
            elif line.importe_divisa:
                local = abs(line.importe_divisa) * (self.tc if foreign and self.tc else 1.0)
                if line.importe_divisa > 0:
                    debe += local
                else:
                    haber += local
        return debe, haber, imp

    def _get_line_ids(self):
        """Linea de caja: la contrapartida de las facturas (pago: Haber; cobro:
        Debe). Se mantiene una sola y se quitan las que quedaron en cero."""
        if self.invoice_ids and self.journal_id:
            debe, haber, imp = self._fx_invoice_totals()
            net = round(debe - haber, 2)
            vals = {
                'account_id': self.journal_id.default_debit_account_id.id,
                'currency_id': self.journal_id.currency_id.id if self.journal_id.currency_id else None,
                'importe_divisa': round(-imp, 2),
                'debe': -net if net < 0 else 0.0,
                'haber': net if net > 0 else 0.0,
            }
            zero = self.lines_ids.filtered(lambda l: not l.debe and not l.haber and not l.importe_divisa)
            if zero:
                zero.unlink()
            if not self.lines_ids:
                self.env['multipayment.advance.it.line2'].create(dict(vals, main_id=self.id))
            elif len(self.lines_ids) == 1:
                self.lines_ids[0].write(vals)

    def calculate_line(self):
        """«Calcular» agrega una linea que cuadra el asiento: si ya cuadra, no
        agrega nada (antes dejaba una linea en cero)."""
        amount = sum(l.debe - l.haber for l in self.invoice_ids) + sum(l.debe - l.haber for l in self.lines_ids)
        if abs(amount) < 0.005:
            return True
        return super(MultipaymentAdvanceIt, self).calculate_line()

    @api.model
    def create(self, vals):
        res = super(MultipaymentAdvanceIt, self).create(vals)
        res._get_line_ids()
        if not res.nro_operation:
            res.nro_operation = res.name
        return res

    def write(self, vals):
        res = super(MultipaymentAdvanceIt, self).write(vals)
        self._get_line_ids()
        return res


class MultipaymentAdvanceItLine(models.Model):
    _inherit = 'multipayment.advance.it.line'

    type_operation = fields.Many2one('type.operation', string='Type of Operation')
    type_good_service = fields.Many2one('einvoice.catalog.54', string='Goods and Services')
    partner_bank_acc_id = fields.Many2one('res.partner.bank', string='Cuenta Bancaria')
    journal_id = fields.Many2one('account.journal', related='main_id.journal_id')
    # SFR
    #type_of_account = fields.Selection('res.partner.bank', string='Type of account',related='name.partner_bank_acc_id.type_of_account')
    type_of_account = fields.Selection(string='Tipo', related='partner_bank_acc_id.type_of_account')
    bank_curr_id = fields.Many2one(string="Mon",  related='partner_bank_acc_id.currency_id')
    bank_id = fields.Many2one('res.bank', related='partner_bank_acc_id.bank_id')
    # En Odoo 13 las lineas en soles no llevan moneda (solo las de moneda
    # extranjera), asi que la columna Moneda salia vacia en facturas y letras en
    # soles. currency_id NO se toca: el asiento la usa para decidir si la linea
    # va en moneda extranjera. Esta es solo para mostrar.
    currency_display_id = fields.Many2one('res.currency', string='Moneda', compute='_compute_currency_display_id')
    # Tipo de factura del documento pagado (factura o letra)
    type_invoice = fields.Selection(related='invoice_id.type_invoice', string='Tipo de factura', readonly=True)

    @api.depends('invoice_id.currency_id', 'invoice_id.move_id.currency_id')
    def _compute_currency_display_id(self):
        for line in self:
            line.currency_display_id = line.invoice_id.currency_id or line.invoice_id.move_id.currency_id \
                or line.main_id.company_id.currency_id

    # @api.onchange('debe')
    # def _onchange_debe(self):
    # 	self.main_id.lines_ids[0].importe_divisa = round(sum(self.main_id.invoice_ids.mapped('debe')) / self.main_id.tc, 2)* -1

    def _get_partner_bank_account(self, is_detraction=False):
        if self.partner_id and self.journal_id:
            acc = self.env['multipayment.advance.it'].get_acc(self.partner_id, self.journal_id, is_detraction)
            self.partner_bank_acc_id = acc.id if acc else None

    @api.onchange('invoice_id')
    def on_change_invoice_id(self):
        if self.invoice_id:
            residual_amount = 0
            if self.invoice_id.currency_id:
                residual_amount = self.invoice_id.amount_residual_currency
            else:
                residual_amount = self.invoice_id.amount_residual
            self.saldo = residual_amount
            self.operation_type = self.invoice_id.move_id.type_op_det
            self.good_services = self.invoice_id.move_id.code_operation
            self.importe_divisa = residual_amount
            self._update_debit_credit()
