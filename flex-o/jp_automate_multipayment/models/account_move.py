from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_round
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    type_operation = fields.Many2one('type.operation', copy=False, string='Type of Operation')
    type_good_service = fields.Many2one('einvoice.catalog.54', copy=False, string='Goods and Services')
    type_op_det = fields.Char(string=u'Tipo de Operación', size=2, copy=False, related='type_operation.name')
    code_operation = fields.Char(string=u'Bien o Servicio', size=5, copy=False, related='type_good_service.code')
    percent_detraction = fields.Float(string='Porcentaje de Detraccion', copy=False)
    referencial_value = fields.Float(string='Valor Referencial')

    retencion_amount = fields.Float(string='Monto de Retencion')
    p_retention = fields.Float(string='% de Retencion', readonly=True)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        self._onchange_detraction_partner_id()
        self._onchange_percent_detraction()
        self._onchange_linked_to_detractions()
        return res

    def post(self):
        rec = super(AccountMove, self).post()
        self._onchange_detraction_partner_id()
        self._onchange_percent_detraction()
        self._onchange_linked_to_detractions()
        return rec

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        res = super(AccountMove, self)._compute_amount()
        #URO comentado porque no permite realizar pagos de facturas cuando el periodo de las mismas esta cerrado
        # SFR se descomenta porque no calcula detracciones en borrador al guardar.
        for rec in self:
            if rec.state == 'draft':
                rec._onchange_percent_detraction()
                rec._onchange_linked_to_detractions()
        return res

    @api.onchange('partner_id', 'invoice_line_ids')
    def _onchange_detraction_partner_id(self):
        for rec in self:
            if any(i.product_id.type_operation and i.product_id.type_good_service for i in rec.invoice_line_ids):
                lines = rec.invoice_line_ids.filtered(lambda l: l.product_id.type_operation)
                var = 0
                for line in lines:
                    if var == 0:
                        if line.product_id.type_good_service.percentage > var:
                            var = line
                    else:
                        if line.product_id.type_good_service.percentage > var.product_id.type_good_service.percentage:
                            var = line
                if var != 0:
                    rec.type_operation = var.product_id.type_operation
                    rec.type_good_service = var.product_id.type_good_service
            else:
                if rec.partner_id.type_operation and rec.partner_id.type_good_service:
                    rec.type_operation = rec.partner_id.type_operation
                    rec.type_good_service = rec.partner_id.type_good_service
                else:
                    products = rec.invoice_line_ids.filtered(lambda l: l.product_id.id is not False)
                    if len(products) > 0:
                        rec.type_operation = False
                        rec.type_good_service = False

            rec._onchange_type_good_service()

    @api.onchange('type_good_service', 'currency_id', 'currency_rate')
    def _onchange_type_good_service(self):
        for rec in self:
            if rec.type_good_service.percentage:
                rec.percent_detraction = rec.type_good_service.percentage
                rec._onchange_percent_detraction()

    @api.onchange('percent_detraction', 'amount_total')
    def _onchange_percent_detraction(self):
        for rec in self:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            decimals = MainParameter.round_detractions
            ReportBase = self.env['report.base']
            if rec.amount_total > 0:
                # Si Doc. es en ME
                if rec.currency_id != self.env.company.currency_id and rec.currency_rate != 0:
                    ref_amount = round(rec.referencial_value/rec.currency_rate * rec.percent_detraction / 100,2) 
                    rec.detra_amount = ref_amount if round(rec.referencial_value / rec.currency_rate, 2) > rec.amount_total else round(rec.amount_total * rec.percent_detraction / 100,2)
                    rec.detraction_amount = ReportBase.custom_round(rec.detra_amount*rec.currency_rate,decimals=decimals)
                    #rec.detraction_amount = ReportBase.custom_round(rec.detra_amount,decimals=decimals) if decimals > 0 else ReportBase.custom_round(rec.detraction_amount)
                else:
                    # Si Doc es en MN
                    ref_amount = round(rec.referencial_value * rec.percent_detraction/100, decimals)
                    rec.detra_amount = ref_amount if rec.referencial_value > rec.amount_total else round(rec.amount_total * rec.percent_detraction / 100, decimals)
                    rec.detraction_amount = rec.detra_amount if rec.detra_amount>0 else 0.00
                    #rec.detraction_amount = round(abs(rec.amount_total_signed) * (float(rec.percent_detraction) / 100.0), 2)

    # URO comentado porque no permite realizar pagos de facturas cuando el periodo de las mismas esta cerrado
    # @api.constrains('amount_total', 'type_document_id')
    def _constrains_linked_to_detractions(self):
        for rec in self:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            decimals = MainParameter.round_detractions
            ReportBase = self.env['report.base']
            if rec.journal_id.register_sunat and rec.type_document_id in MainParameter.detraction_doc_ids:
                if rec.linked_to_detractions:
                    products = rec.invoice_line_ids.filtered(lambda l: l.product_id.id is False)
                    if len(products) != len(rec.invoice_line_ids):
                        inv_amount = rec.amount_total if rec.currency_id == self.env.company.currency_id else rec.amount_total * rec.currency_rate
                        # rec.linked_to_detractions = False
                        # rec.percent_detraction = 0
                        # rec.detra_amount = 0
                        # rec.type_good_service =  False
                        # rec.type_operation = False
                        # rec.detraction_payment_id = False
                        if MainParameter.limit_line_ids:
                            for line in MainParameter.limit_line_ids:
                                for item in rec.invoice_line_ids:
                                    # if item.product_id.id is not False:
                                    if item.product_id.type_good_service in line.catalog_54_ids:
                                        if inv_amount > line.amount and rec.percent_detraction < item.product_id.type_good_service.percentage:
                                            rec.linked_to_detractions = True
                                            rec.percent_detraction = item.product_id.type_good_service.percentage
                                            rec.type_operation = item.product_id.type_operation.id
                                            rec.type_good_service = item.product_id.type_good_service.id

                                            # Si Doc. es en ME
                                            if rec.currency_id != self.env.company.currency_id and rec.currency_rate != 0:
                                                ref_amount = round(rec.referencial_value/rec.currency_rate * rec.percent_detraction/100,2)
                                                rec.detra_amount = ref_amount if round(rec.referencial_value/rec.currency_rate,2)>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,2)
                                                rec.detraction_amount = ReportBase.custom_round(rec.detra_amount*rec.currency_rate,decimals=decimals)
                                                #rec.detraction_amount = ReportBase.custom_round(rec.detra_amount,decimals=decimals) if decimals > 0 else ReportBase.custom_round(rec.detraction_amount)
                                            else:
                                                # Si Doc es en MN
                                                ref_amount = round(rec.referencial_value * rec.percent_detraction/100, decimals)
                                                rec.detra_amount = ref_amount if rec.referencial_value>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,decimals)
                                                rec.detraction_amount = rec.detra_amount if rec.detra_amount > 0 else 0.00
                                                #rec.detraction_amount = round(abs(rec.amount_total_signed) * (float(rec.percent_detraction) / 100.0), 2)

                                            rec.detraction_payment_id = MainParameter.defaul_detraction_payment_id.id  # parametrizar medio de pago x defecto SFR
                                            rec.detraction_type_id = item.product_id.type_good_service.id
                                            rec.op_type_sunat_id = MainParameter.defaul_detracionts.id  # Actualzar de acuerdo a parametro de ver modulos Itgrupo

                else:
                    products = rec.invoice_line_ids.filtered(lambda l: l.product_id.id is False)
                    if len(products) != len(rec.invoice_line_ids):
                        inv_amount = rec.amount_total if rec.currency_id == self.env.company.currency_id else rec.amount_total * rec.currency_rate
                        rec.linked_to_detractions = False
                        rec.percent_detraction = 0
                        rec.detra_amount = 0
                        rec.type_good_service = False
                        rec.type_operation = False
                        rec.detraction_payment_id = False
                        if MainParameter.limit_line_ids:
                            for line in MainParameter.limit_line_ids:
                                for item in rec.invoice_line_ids:
                                    # if item.product_id.id is not False:
                                    if item.product_id.type_good_service in line.catalog_54_ids:
                                        if inv_amount > line.amount and rec.percent_detraction < item.product_id.type_good_service.percentage:
                                            rec.linked_to_detractions = True
                                            rec.percent_detraction = item.product_id.type_good_service.percentage
                                            rec.type_operation = item.product_id.type_operation.id
                                            rec.type_good_service = item.product_id.type_good_service.id

                                            # Si Doc. es en ME
                                            if rec.currency_id != self.env.company.currency_id and rec.currency_rate != 0:
                                                ref_amount = round(rec.referencial_value/rec.currency_rate * rec.percent_detraction/100,2)
                                                rec.detra_amount = ref_amount if round(rec.referencial_value/rec.currency_rate,2)>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,2)
                                                rec.detraction_amount = ReportBase.custom_round(rec.detra_amount*rec.currency_rate,decimals=decimals)
                                                #rec.detraction_amount = ReportBase.custom_round(rec.detra_amount,decimals=decimals) if decimals > 0 else ReportBase.custom_round(rec.detraction_amount)
                                            else:
                                                # Si Doc es en MN
                                                ref_amount = round(rec.referencial_value * rec.percent_detraction/100, decimals)
                                                rec.detra_amount = ref_amount if rec.referencial_value>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,decimals)
                                                rec.detraction_amount = rec.detra_amount if rec.detra_amount>0 else 0.00
                                                #rec.detraction_amount = round(abs(rec.amount_total_signed) * (float(rec.percent_detraction) / 100.0), 2)

                                            rec.detraction_payment_id = MainParameter.defaul_detraction_payment_id.id  # parametrizar medio de pago x defecto SFR
                                            rec.detraction_type_id = item.product_id.type_good_service.id
                                            rec.op_type_sunat_id = MainParameter.defaul_detracionts.id  # Actualzar de acuerdo a parametro de ver modulos Itgrupo
            else:
                rec.linked_to_detractions = False

        #SFR Si no est[a afecto de detraccion y partner es agente de Retencion
        # El procedimiento en pagina de sunat con Clave Sol es distinta, las retenciones y detracciones siempre en PEN, cuando los Documentos en USD
        # En los aplicativos siempre debe ser en moneda de documento
        if not self.linked_to_detractions and self.partner_id.retention_agent:
            MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
            decimals = MainParameter.round_detractions
            if MainParameter.p_retention == 0 or MainParameter.min_amount == 0:
                raise UserError(
                    u'% de retencion y/o monto minimo retencion no est a configurado en parametros generales pestaña Retenciones')
            self.p_retention = MainParameter.p_retention
            min_amount = MainParameter.min_amount
            self.detraction_amunt = 0

            ret_amount = round(abs(self.amount_total) * self.p_retention / 100.0, 2)

            # Si Doc. es en ME
            if self.currency_id != self.env.company.currency_id and self.currency_rate != 0:
                self.retencion_amount = ret_amount if round(self.amount_total*self.currency_rate,2)>=min_amount else 0
            else:
                # Si Doc es en MN
                self.retencion_amount = ret_amount if self.amount_total >= min_amount else 0


    @api.onchange('amount_total', 'type_document_id')
    def _onchange_linked_to_detractions(self):
        self._constrains_linked_to_detractions()

    def get_import_txt_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'get.invoices.wizard',
            'views': [[self.env.ref('jp_automate_multipayment.move_txt_wizard').id, 'form']],
            'context': self._context,
            'target': 'new',
        }

    def create_detraccion_gastos(self):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        decimals = MainParameter.round_detractions
        if MainParameter.auto_detractions_clients or MainParameter.auto_detractions_suppliers:
            raise UserError(
                u'Para utilizar este boton desmarque el check de automatizacion de detracciones clientes y proveedores en Parametros Principales')
        # if not self.journal_id.register_sunat:
        #     raise UserError('El diario del documento %s no tiene registro sunat' % self.ref)
        pretention = self.percent_detraction / 100 if self.percent_detraction else 1
        Line = MainParameter.limit_line_ids.filtered(lambda l: self.type_good_service in l.catalog_54_ids)
        if not Line:
            raise UserError(
                'No se ha encontrado una linea con el tipo de operacion %s en la pestaña detracciones de parametros principales' % self.type_good_service.name)
        if self.referencial_value and self.referencial_value < Line[0].amount:
            raise UserError(
                'El monto referencial no es mayor al monto minimo de %d configurado en parametros' % Line[0].amount)

        if self.amount_total > 0:
            detra_amount = self.detra_amount
            # Si Doc. es en ME
            #if rec.currency_id != self.env.company.currency_id and rec.currency_rate != 0:
            #    ref_amount = round(rec.referencial_value/rec.currency_rate * rec.percent_detraction/100,2)
            #    rec.detra_amount = ref_amount if round(rec.referencial_value/rec.currency_rate,2)>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,2)
            #else:
                # Si Doc es en MN
            #    ref_amount = round(rec.referencial_value * rec.percent_detraction/100, decimals)
            #    rec.detra_amount = ref_amount if rec.referencial_value>rec.amount_total else round(rec.amount_total * rec.percent_detraction/100,decimals)

        context = {
            'invoice_id': self.id,
            'default_fecha': fields.Date.today(),
            'default_monto': detra_amount,
        }
        return {
            'type': 'ir.actions.act_window',
            'name': "Generar Detracción",
            'view_type': 'form',
            'view_mode': 'form',
            'context': context,
            'res_model': 'account.detractions.wizard',
            'target': 'new',
        }

    def action_post(self):
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        decimals = MainParameter.round_detractions
        self._constrains_linked_to_detractions()
        ReportBase = self.env['report.base']

        if self.currency_id == self.env.company.currency_id:
            amount = ReportBase.custom_round(self.detra_amount,
                                             decimals=decimals) if decimals > 0 else ReportBase.custom_round(
                self.detra_amount, decimals=decimals)
            inv_amount = self.amount_total
        else:
            amount = self.detra_amount
            inv_amount = self.amount_total * self.currency_rate

        if not MainParameter.limit_line_ids:
            raise UserError('Falta configurar valores limite  en Parametros Principales en la pestaña Detracciones')
        for line in MainParameter.limit_line_ids:
            if self.type_good_service in line.catalog_54_ids:
                detraction_limit = line.amount
                break
            else:
                detraction_limit = 0
        res = super(AccountMove, self).action_post()
        flag = False
        if MainParameter.auto_detractions_clients and self.type in ['out_invoice', 'out_refund']:
            flag = True
        if MainParameter.auto_detractions_suppliers and self.type in ['in_invoice', 'in_refund']:
            flag = True
        if self.referencial_value:
            inv_amount = self.referencial_value
        if self.linked_to_detractions and flag and not self.move_detraccion_id and inv_amount >= detraction_limit and self.journal_id.register_sunat:
            pretention = self.percent_detraction / 100 if self.percent_detraction else 1
            wizard = self.env['account.detractions.wizard'].create({
                'fecha': self.invoice_date,
                'monto': amount if not self.referencial_value else float_round(self.referencial_value * pretention, 2),
            })
            context = {
                'invoice_id': self.id,
                'default_fecha': self.invoice_date,
                'default_monto': amount,
            }
            wizard.with_context(context).generar()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    advance_id = fields.Many2one('multipayment.advance.it')
    date_detraccion = fields.Date(related='move_id.date_detraccion', string='Fecha de Detraccion')
    voucher_number = fields.Char(related='move_id.voucher_number', stirng='Numero de Comprobante de Detraccion')


class AccountDetractionsWizard(models.TransientModel):
    _inherit = 'account.detractions.wizard'

    def generar(self):
        invoice = self.env['account.move'].browse(self.env.context['invoice_id'])
        m = self.env['main.parameter'].search([('company_id', '=', invoice.company_id.id)], limit=1)
        if invoice.type_document_id not in m.detraction_doc_ids:
            raise UserError('El tipo de documento de la factura %s no esta afecto a detracciones' % invoice.name)

        if not m.detraction_journal.id:
            raise UserError(
                u"No esta configurada el Diario de Detracción en Parametros Principales de Contabilidad para su Compañía")

        if not invoice.type_op_det or not invoice.code_operation:
            raise UserError(u"El campo 'Tipo de Operación' y 'Bien o Servicio' no pueden estar vacíos")

        flag_ver = True
        data = {
            'journal_id': m.detraction_journal.id,
            'ref': (invoice.ref if invoice.ref else 'Borrador'),
            'date': self.fecha,
            'company_id': invoice.company_id.id,
            'glosa': 'PROVISION DE LA DETRACCION DE LA FACTURA ' + invoice.ref,
            'currency_rate': invoice.currency_rate,
            'type_op_det': invoice.type_op_det,
            'code_operation': invoice.code_operation,
        }
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
        if invoice.type == 'in_invoice':
            if not m.detractions_account.id:
                raise UserError(
                    u"No esta configurada la Cuenta de Detracción para Proveedor en Parametros Principales de Contabilidad para su Compañía")
            if invoice.currency_id.name == 'USD':
                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': self.env['report.base'].custom_round(self.monto * invoice.currency_rate),
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'currency_id': invoice.currency_id.id,
                    'amount_currency': self.monto,
                    'tc': invoice.currency_rate,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': m.detractions_account.id,
                    'debit': 0,
                    'credit': self.env['report.base'].custom_round(self.monto * invoice.currency_rate),
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

            else:
                line_cc = (0, 0, {
                    'account_id': filtered_line.account_id.id,
                    'debit': self.monto,
                    'credit': 0,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

                line_cc = (0, 0, {
                    'account_id': m.detractions_account.id,
                    'debit': 0,
                    'credit': self.monto,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': doc.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

        if invoice.type == 'out_invoice':
            if not m.customer_account_detractions.id:
                raise UserError(
                    u"No esta configurada la Cuenta de Detracción para Clientes en Parametros Principales de Contabilidad para su Compañía")
            if invoice.currency_id.name == 'USD':
                line_cc = (0, 0, {
                    'account_id': m.customer_account_detractions.id,
                    'debit': self.env['report.base'].custom_round(self.monto * invoice.currency_rate),
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
                    'credit': self.env['report.base'].custom_round(self.monto * invoice.currency_rate),
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

            else:
                line_cc = (0, 0, {
                    'account_id': m.customer_account_detractions.id,
                    'debit': self.monto,
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
                    'credit': self.monto,
                    'name': 'DETRACCION - ' + invoice.ref,
                    'partner_id': invoice.partner_id.id,
                    'nro_comp': invoice.ref,
                    'type_document_id': invoice.type_document_id.id,
                    'company_id': invoice.company_id.id,
                })
                lines.append(line_cc)

        data['line_ids'] = lines
        tt = self.env['account.move'].create(data)
        ids_conciliation = []
        ids_conciliation.append(filtered_line.id)

        for line in tt.line_ids:
            if line.account_id == filtered_line.account_id and line.nro_comp == filtered_line.nro_comp and line.type_document_id == filtered_line.type_document_id and line.partner_id.id == filtered_line.partner_id.id:
                ids_conciliation.append(line.id)

        if len(ids_conciliation) > 1:
            self.env['account.move.line'].browse(ids_conciliation).reconcile()

        tt.type_operation = invoice.type_operation.id
        tt.type_good_service = invoice.type_good_service.id

        tt.write({
            'type_operation': invoice.type_operation.id,
            'type_good_service': invoice.type_good_service.id
        })
        if tt.state == 'draft':
            tt.post()
        invoice.move_detraccion_id = tt.id

        if flag_ver:
            invoice.name_move_detraccion = tt.name

        return True

    def get_txt(self):
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
            self.get_str_number(sum_total), 15, '0', False)
        ctxt += """\r\n"""
        for elem in self.multipayment_id.invoice_ids:
            ctxt += '6' + elem.partner_id.vat + self.get_text_with_size(None, 35, ' ', True) + '000000000'
            code_operation = elem.invoice_id.move_id.type_good_service.code
            ctxt += self.get_text_with_size(code_operation, 3, '0', False)
            acc_bank = self.env['res.partner.bank'].search(
                [('partner_id', '=', elem.partner_id.id), ('is_detraction_account', '=', True),
                 ('company_id', '=', elem.main_id.company_id.id)], limit=1)
            if self.type == 'cp' and acc_bank.acc_number:
                ctxt += self.get_text_with_size(acc_bank.acc_number, 11, '0', False)
            elif self.type == 'cp' and not acc_bank.acc_number:
                raise UserError(u'No configuró la Cuenta de Detracciones para su Partner.')
            else:
                ctxt += ''
            ctxt += self.get_text_with_size(self.get_str_number(elem.debe), 15, '0',
                                            False) if self.type == 'cp' else self.get_text_with_size(
                self.get_str_number(elem.haber), 15, '0', False)
            type_op_det = elem.invoice_id.move_id.type_operation.name
            if not type_op_det:
                raise UserError(u'Debe definir el Tipo de Operación de Detracción en su Factura')
            ctxt += type_op_det
            date = elem.invoice_id.move_id.invoice_date if elem.invoice_id.move_id.invoice_date else elem.invoice_id.move_id.date
            ctxt += str(date.year) + str('{:02d}'.format(date.month))
            ctxt += '01'
            partition = elem.invoice_id.nro_comp.split('-')
            ctxt += self.get_text_with_size(partition[0], 4, '0', False) + self.get_text_with_size(partition[1], 8, '0',
                                                                                                   False)
            ctxt += """\r\n"""

        import importlib
        import sys
        importlib.reload(sys)

        return self.env['popup.it'].get_file(name_doc, base64.encodestring(b'' + ctxt.encode("utf-8")))
