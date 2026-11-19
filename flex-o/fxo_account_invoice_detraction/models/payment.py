import datetime
from odoo import _, api, fields, models
from odoo.exceptions import Warning, ValidationError
MAP_INVOICE_TYPE_PARTNER_TYPE = {'out_invoice':'customer', 
 'out_refund':'customer', 
 'in_invoice':'supplier', 
 'in_refund':'supplier'}


class AccountPaymentMasive(models.TransientModel):
    _name = 'account.payment.masive'

    name = fields.Char('Pagos Masivos',default='None')

    def crear_detraction(self):
        self.env['account.move'].browse(self.env.context['active_ids']).create_detraccion_masive()

class Product_Product(models.Model):
    _inherit = 'product.product'

    is_detraction = fields.Boolean(string='Tiene Detraccion?')    
    detraction_percent = fields.Float(string='Percentage', default=12.0)
    type_operation = fields.Selection([
     ('01', '01 - Venta de bienes o prestación de servicios'),
     ('02', '02 - Retiro de bienes'),
     ('03', '03 - Traslados que no son venta'),
     ('04', '04 - Venta a través de la Bolsa de Productos'),
     ('05', '05 - Venta de Bienes exonerados del IGV'),
     ('09', '09 - Pago Ley N° 30737')])
    
    type_good_service = fields.Selection([
     ('001', '001 - Azúcar y melaza de caña'),
     ('002', '002 - Arroz'),
     ('003', '003 - Alcohol etílico'),
     ('004', '004 - Recursos hidrobiológicos'),
     ('005', '005 - Maíz amarillo duro'),
     ('007', '007 - Caña de azúcar'),
     ('008', '008 - Madera'),
     ('009', '009 - Arena y piedra.'),
     ('010', '010 - Residuos, subproductos, desechos, recortes y desperdicios'),
     ('011', '011 - Bienes gravados con el IGV, o renuncia a la exoneración'),
     ('012', '012 - Intermediación laboral y tercerización'),
     ('013', '013 - Animales vivos'),
     ('014', '014 - Carnes y despojos comestibles'),
     ('015', '015 - Abonos, cueros y pieles de origen animal'),
     ('016', '016 - Aceite de pescado'),
     ('017', '017 - Harina, polvo y “pellets” de pescado, crustáceos, moluscos y demás invertebrados acuáticos'),
     ('019', '019 - Arrendamiento de bienes muebles'),
     ('020', '020 - Mantenimiento y reparación de bienes muebles'),
     ('021', '021 - Movimiento de carga'),
     ('022', '022 - Otros servicios empresariales'),
     ('024', '024 - Comisión mercantil'),
     ('025', '025 - Fabricación de bienes por encargo'),
     ('026', '026 - Servicio de transporte de personas'),
     ('027', '027 - Servicio de transporte de carga'),
     ('028', '028 - Transporte de pasajeros'),
     ('030', '030 - Contratos de construcción'),
     ('031', '031 - Oro gravado con el IGV'),
     ('034', '034 - Minerales metálicos no auríferos'),
     ('035', '035 - Bienes exonerados del IGV'),
     ('036', '036 - Oro y demás minerales metálicos exonerados del IGV'),
     ('037', '037 - Demás servicios gravados con el IGV'),
     ('039', '039 - Minerales no metálicos'),
     ('040', '040 - Bien inmueble gravado con IGV')])



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    detraction_percent = fields.Float(string='Percentage', default=12.0)
    detraction_amount = fields.Float(string='Detraction amount')
    round_amount = fields.Boolean(string='Round Amount', default=True)
    is_detraction = fields.Boolean(string='Is detraction?')
    detraction_state = fields.Selection(string='Detraction state', selection=[('0', 'Unpaid'), ('1', 'Paid')], default='0', track_visibility='always')
    detraction_lot_id = fields.Many2one(comodel_name='detraction.create.file', string='Detraction Lot')
    account_amount = fields.Float(string='Account amount')
    type_operation = fields.Selection([
     ('01', '01 - Venta de bienes o prestación de servicios'),
     ('02', '02 - Retiro de bienes'),
     ('03', '03 - Traslados que no son venta'),
     ('04', '04 - Venta a través de la Bolsa de Productos'),
     ('05', '05 - Venta de Bienes exonerados del IGV'),
     ('09', '09 - Pago Ley N° 30737')])
    type_good_service = fields.Selection([
     ('001', '001 - Azúcar y melaza de caña'),
     ('002', '002 - Arroz'),
     ('003', '003 - Alcohol etílico'),
     ('004', '004 - Recursos hidrobiológicos'),
     ('005', '005 - Maíz amarillo duro'),
     ('007', '007 - Caña de azúcar'),
     ('008', '008 - Madera'),
     ('009', '009 - Arena y piedra.'),
     ('010', '010 - Residuos, subproductos, desechos, recortes y desperdicios'),
     ('011', '011 - Bienes gravados con el IGV, o renuncia a la exoneración'),
     ('012', '012 - Intermediación laboral y tercerización'),
     ('013', '013 - Animales vivos'),
     ('014', '014 - Carnes y despojos comestibles'),
     ('015', '015 - Abonos, cueros y pieles de origen animal'),
     ('016', '016 - Aceite de pescado'),
     ('017', '017 - Harina, polvo y “pellets” de pescado, crustáceos, moluscos y demás invertebrados acuáticos'),
     ('019', '019 - Arrendamiento de bienes muebles'),
     ('020', '020 - Mantenimiento y reparación de bienes muebles'),
     ('021', '021 - Movimiento de carga'),
     ('022', '022 - Otros servicios empresariales'),
     ('024', '024 - Comisión mercantil'),
     ('025', '025 - Fabricación de bienes por encargo'),
     ('026', '026 - Servicio de transporte de personas'),
     ('027', '027 - Servicio de transporte de carga'),
     ('028', '028 - Transporte de pasajeros'),
     ('030', '030 - Contratos de construcción'),
     ('031', '031 - Oro gravado con el IGV'),
     ('034', '034 - Minerales metálicos no auríferos'),
     ('035', '035 - Bienes exonerados del IGV'),
     ('036', '036 - Oro y demás minerales metálicos exonerados del IGV'),
     ('037', '037 - Demás servicios gravados con el IGV'),
     ('039', '039 - Minerales no metálicos'),
     ('040', '040 - Bien inmueble gravado con IGV')])

    # def default_get(self, default_fields):
    #     rec = super(AccountPayment, self).default_get(default_fields)
    #     if self.is_detraction:
    #         amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date) * (self.detraction_percent / 100)
    #         rec.update({
    #             'is_detraction':self.is_detraction, 
    #             'type_operation':self.type_operation, 
    #             'type_good_service':self.type_good_service,
    #             'amount': abs(amount),
    #         })
    #     return rec

    @api.onchange('amount', 'currency_id')
    def _onchange_amount(self):
        res = super(AccountPayment, self)._onchange_amount()
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types))]
        for x in jrnl_filters['domain']:
            domain_on_types.append(x)
        #domain_on_types.append(x for x in jrnl_filters['domain'])
        if self.is_detraction:
            self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)
        return res

    def _compute_journal_domain_and_types(self):
        res = super(AccountPayment, self)._compute_journal_domain_and_types()
        if self.is_detraction:
            res['domain'].append(('bank_account_id.type_of_account', '=', '2'))
        return res

    @api.onchange('detraction_percent', 'is_detraction', 'round_amount')
    def _onchange_percentage(self):
        # amount = self.amount
        if self.is_detraction:
            active_ids = self._context.get('active_ids')
            self.payment_date = self.env['account.move'].search([('id', 'in', active_ids)]).invoice_date
            amount = 0
            for inv in self.invoice_ids:
                amount += inv.amount_total

            if self.detraction_percent:
                if self.round_amount:
                    rounded_total = self.amount * (self.detraction_percent / 100)
                    if rounded_total - int(rounded_total) >= 0.5:
                        self.detraction_amount = int(self.amount * (self.detraction_percent / 100)) + 1
                    else:
                        self.detraction_amount = int(self.amount * (self.detraction_percent / 100))
                else:
                    self.detraction_amount = self.amount * (self.detraction_percent / 100)
            self.payment_difference = (abs(self._compute_payment_amount(self.invoice_ids, self.invoice_ids[0].currency_id, self.invoice_ids[0].journal_id, self.payment_date or fields.Date.today())) - self.detraction_amount) * -1
            #self.amount = abs(self._compute_payment_amount(self.invoice_ids, self.invoice_ids[0].currency_id, self.invoice_ids[0].journal_id, self.payment_date or fields.Date.today()) * (self.detraction_percent / 100))
            self.amount = amount
        else:
            # active_ids = self._context.get('active_ids')
            # invoices = self.env['account.move'].browse(active_ids)
            self.amount = abs(self._compute_payment_amount(self.invoice_ids, self.invoice_ids[0].currency_id, self.invoice_ids[0].journal_id, self.payment_date or fields.Date.today()))
        
    def post(self):
        for payment in self:
            if payment.is_detraction:
                payment.amount = payment.detraction_amount
                for invoice in payment.invoice_ids:
                    invoice.detraction_privisioned = True

        res = super(AccountPayment, self).post()
        for payment in self:
            payment.account_amount = 0
            for ml in payment.move_line_ids:
                payment.account_amount += round(ml.debit, 0)

        return res

    def pay(self):
        self.detraction_state = '1'

    def unpay(self):
        self.detraction_state = '0'


class payment_register(models.TransientModel):
    _inherit = 'account.payment.register'

    detraction_percent = fields.Float(string='Percentage', default=12.0)
    detraction_amount = fields.Float(string='Detraction amount')
    round_amount = fields.Boolean(string='Round Amount', default=True)
    is_detraction = fields.Boolean(string='Is detraction?')
    type_operation = fields.Selection([
     ('01', '01 - Venta de bienes o prestación de servicios'),
     ('02', '02 - Retiro de bienes'),
     ('03', '03 - Traslados que no son venta'),
     ('04', '04 - Venta a través de la Bolsa de Productos'),
     ('05', '05 - Venta de Bienes exonerados del IGV'),
     ('09', '09 - Pago Ley N° 30737')])
    type_good_service = fields.Selection([
     ('001', '001 - Azúcar y melaza de caña'),
     ('002', '002 - Arroz'),
     ('003', '003 - Alcohol etílico'),
     ('004', '004 - Recursos hidrobiológicos'),
     ('005', '005 - Maíz amarillo duro'),
     ('007', '007 - Caña de azúcar'),
     ('008', '008 - Madera'),
     ('009', '009 - Arena y piedra.'),
     ('010', '010 - Residuos, subproductos, desechos, recortes y desperdicios'),
     ('011', '011 - Bienes gravados con el IGV, o renuncia a la exoneración'),
     ('012', '012 - Intermediación laboral y tercerización'),
     ('013', '013 - Animales vivos'),
     ('014', '014 - Carnes y despojos comestibles'),
     ('015', '015 - Abonos, cueros y pieles de origen animal'),
     ('016', '016 - Aceite de pescado'),
     ('017', '017 - Harina, polvo y “pellets” de pescado, crustáceos, moluscos y demás invertebrados acuáticos'),
     ('019', '019 - Arrendamiento de bienes muebles'),
     ('020', '020 - Mantenimiento y reparación de bienes muebles'),
     ('021', '021 - Movimiento de carga'),
     ('022', '022 - Otros servicios empresariales'),
     ('024', '024 - Comisión mercantil'),
     ('025', '025 - Fabricación de bienes por encargo'),
     ('026', '026 - Servicio de transporte de personas'),
     ('027', '027 - Servicio de transporte de carga'),
     ('028', '028 - Transporte de pasajeros'),
     ('030', '030 - Contratos de construcción'),
     ('031', '031 - Oro gravado con el IGV'),
     ('034', '034 - Minerales metálicos no auríferos'),
     ('035', '035 - Bienes exonerados del IGV'),
     ('036', '036 - Oro y demás minerales metálicos exonerados del IGV'),
     ('037', '037 - Demás servicios gravados con el IGV'),
     ('039', '039 - Minerales no metálicos'),
     ('040', '040 - Bien inmueble gravado con IGV')])

    # @api.onchange('detraction_percent', 'is_detraction', 'round_amount')
    # def _onchange_percentage(self):
    #     amount = self.amount
    #     if self.is_detraction:
    #         self.amount = 0
    #         for inv in self.invoice_ids:
    #             self.amount += inv.amount_total

    #         if self.detraction_percent:
    #             if self.round_amount:
    #                 rounded_total = self.amount * (self.detraction_percent / 100)
    #                 if rounded_total - int(rounded_total) >= 0.5:
    #                     self.detraction_amount = int(self.amount * (self.detraction_percent / 100)) + 1
    #                 else:
    #                     self.detraction_amount = int(self.amount * (self.detraction_percent / 100))
    #             else:
    #                 self.detraction_amount = self.amount * (self.detraction_percent / 100)
    #         self.payment_difference = (amount - self.detraction_amount) * -1
    #     else:
    #         active_ids = self._context.get('active_ids')
    #         invoices = self.env['account.move'].browse(active_ids)
    #         self.amount = abs(self._compute_payment_amount(invoices))

    # def get_payments_vals(self):
    #     """Compute the values for payments
    #        Jean Paul added even if it is a detraction payment.

    #     :return: a list of payment values (dictionary).
    #     """
    #     grouped = defaultdict(lambda: self.env["account.move"])
    #     for inv in self.invoice_ids:
    #         if self.group_payment:
    #             grouped[(inv.commercial_partner_id, inv.currency_id, inv.invoice_partner_bank_id, MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type])] += inv
    #         else:
    #             grouped[inv.id] += inv
    #     return [self._prepare_payment_vals(invoices) for invoices in grouped.values()]

        # if self.multi:
        #     groups = self._groupby_invoices()
        #     return [self._prepare_payment_vals(invoices) for invoices in groups.values()]
        # elif self.is_detraction:
        #     groups = self._groupby_invoices()
        #     return [self._prepare_payment_vals_detractions(invoices) for invoices in groups.values()]
        # else:
        #     return [self._prepare_payment_vals(self.invoice_ids)]

    # def _prepare_payment_vals(self, invoices):
    #     values = {}
    #     res = super(payment_register,self)._prepare_payment_vals(invoices)
    #     if self.is_detraction:
    #         #amount = invoices.amount_total / self.amount * self.detraction_amount
    #         amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date) * (self.detraction_percent / 100)
    #         values.update({
    #                 'is_detraction':self.is_detraction, 
    #                 'type_operation':self.type_operation, 
    #                 'type_good_service':self.type_good_service,
    #                 'amount':abs(amount)})
    #     return res

    def _prepare_payment_vals(self, invoices):
        res = super(payment_register, self)._prepare_payment_vals(invoices)
        if self.is_detraction:
            amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date) * (self.detraction_percent / 100)
            res.update({
                'is_detraction': True, 
                'type_operation': self.type_operation, 
                'type_good_service': self.type_good_service,
                'amount': abs(amount),
                'detraction_amount': abs(amount),
            })
        return res

    def create_payments(self):
        for inv in self.invoice_ids:
            if self.is_detraction == True and inv.detraction_privisioned == True:
                raise  ValidationError(_('The invoice selected for payment already has the detraction provisioned. Invoice number: %s' % inv.name))
            # else:
            #     inv.detraction_privisioned = True
        res = super(payment_register, self).create_payments()
        return res

    @api.onchange('journal_id', 'invoice_ids')
    def _onchange_journal(self):
        res = super(payment_register, self)._onchange_journal()
        if self.is_detraction:
            res['domain']['journal_id'].append(('bank_account_id.type_of_account', '=', '2'))
            self.journal_id = self.env['account.journal'].search(res['domain']['journal_id'], limit=1) 
        return res

    # @api.onchange('is_detraction')
    # def _onchange_is_detraction(self):
    #     if self.is_detraction == True:
    #         active_ids = self._context.get('active_ids')
    #         selected_invoices = self.env['account.move'].search([('id', 'in', active_ids)])
    #         for invoice in selected_invoices:
    #             self.payment_date = invoice.invoice_date
    #     else:
    #         self.payment_date = str(datetime.datetime.today())
    #     jrnl_filters = self._compute_journal_domain_and_types()
    #     journal_types = jrnl_filters['journal_types']
    #     domain_on_types = [('type', 'in', list(journal_types))]
    #     if self.journal_id.type not in journal_types:
    #         self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)
    #     return {'domain': {'journal_id': jrnl_filters['domain'] + domain_on_types}}