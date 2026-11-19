# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import Warning
from ast import literal_eval


class res_partner_credit_detail(models.Model):
    _inherit = ['mail.thread']
    _name = "res.partner.credit.detail"
    _order = "process_date desc"

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].get('res.partner.credit.detail')
        vals.update({"name": seq})
        new_id = super(res_partner_credit_detail, self).create(vals)
        return new_id

    _type_process = [
        ("opening_request", "Apertura"),
        ("extension_request", u"Ampliación"),
        #("approval", "Aprobación"),
        ("suspension", u"Suspensión"),
        ("lift_suspension", u"Levantar suspensión"),
        ("annulment", u"Anulación")
    ]

    _states = (
        ("draft", "Borrador"),
        ("confirmed", "Confirmado"),
        ("approve", "Aprobado"),
        ("rejected", "Rechazado"),
        ("cancel", "Cancelado")
    )

    def _get_user_id(self):
        return self.env.user.id

    
    def _get_currency_id(self):
        self.ensure_one()
        self.show_currency_id = self.currency_id

    partner_id = fields.Many2one("res.partner", string="Cliente", required=True, readonly=True, states={'draft':[('readonly', False)]}, domain=[("is_customer","=", True)])
    process_type = fields.Selection(_type_process, string="Tipo de proceso", required=True, states={'draft':[('readonly', False)]}, default='opening_request')
    process_date = fields.Datetime(string="Fecha de Operación", default=fields.Datetime.now, required=True, readonly=True, states={'draft':[('readonly', False)]})
    amount_application = fields.Float(string="Importe solicitud", required=True, readonly=True, states={'draft':[('readonly', False)]}, default=0.0)
    currency_id = fields.Many2one("res.currency", string='Moneda')
    show_currency_id = fields.Many2one("res.currency", string='Moneda', compute="_get_currency_id")
    amount_debit = fields.Float(string="Importe aprobado", readonly=True, states={'confirmed':[('readonly', False),('required', True)]}, default=0.0)
    amount_credit = fields.Float(string="Importe Anulado", readonly=True, default=0.0)
    state = fields.Selection(_states, string="State", default="draft", track_visibility='onchange')
    user_id = fields.Many2one("res.users", string="Usuario", help="Usuario que realiza la acción", default=_get_user_id)
    note = fields.Text(string="Nota", readonly=True, states={'draft':[('readonly', False)]})
    name = fields.Char(string="Name", default="/", track_visibility='onchange',)
    notes_approval = fields.Text(string="Nota de Aprobación", readonly=True, states={'confirmed':[('readonly', False)]})
    credit_detail_bank_ids = fields.One2many("res.partner.credit.detail.bank", "credit_detail_id", string="Referencias bancarias", readonly=True, states={'draft':[('readonly', False)], 'confirmed':[('readonly', False)]})
    credit_detail_commercial_ids = fields.One2many("res.partner.credit.detail.commercial", "credit_detail_id", string="Referencias comerciales", readonly=True, states={'draft':[('readonly', False)], 'confirmed':[('readonly', False)]})
    credit_detail_finantial_ids = fields.One2many("res.partner.credit.detail.finantial", "credit_detail_id", string="Referencias financieras", readonly=True, states={'draft':[('readonly', False)], 'confirmed':[('readonly', False)]})

    # No permite hacer la aprobación con diferentes monedas
    # ejemplo: si cliente tiene un determinada moneda solo con ese tipo se puede hacer la aprobación
    
    def fconfirm(self):
        self.ensure_one()
        if self.process_type in ["suspension", "lift_suspension", "annulment"]:
            self.write({"state": "confirmed", "amount_application": 0.0, "amount_debit": 0.0, "amount_credit": 0.0})
        else:
            self.write({"state": "confirmed"})
        return True

    def _not_approve_currency_diff(self):
        if self.currency_id.id == self.partner_id.currency_id.id:
            pass
        else:
            raise Warning('No se puede hacer la aprobación con diferentes monedas!')

    # Si amount_debit es menor a cero
    def _amount_debit_zero(self):
        if self.amount_debit <= 0.0:
            raise Warning('Monto cero no puede aprobarse!')

    # Limite de aprobación por usuario
    def _credit_max_approved_user(self, partner):
        res = self.env['res.user.credit.limit'].search_read([('user_id', '=', self._uid)], ["credit_max_approved"])
        if not res:
            raise Warning('Usuario no esta autorizado para realizar aprobación!')
        
        # Get currency default config
        currency_id = literal_eval(self.env["ir.config_parameter"].get_param('nanotec_credit_limit.currency_id', 'False'))
        currency_name_default_config = self.env["res.currency"].browse(currency_id).name

        user_credit_max_approved = res[0].get('credit_max_approved', 0.0)

        if partner.currency_id.name == currency_name_default_config:
            return user_credit_max_approved

        rate = 1

        if partner.currency_id.name == "USD":
            user_credit_max_approved = user_credit_max_approved / rate
        elif partner.currency_id.name == "PEN":
            user_credit_max_approved = user_credit_max_approved * rate
        else:
            raise Warning('Not change other type currency ("PEN", "USD")')

        return user_credit_max_approved

    def verify_approv(self):
        self.ensure_one()
        if self.process_type == 'opening_request':
            self._not_approve_currency_diff()
            self._amount_debit_zero()
            if self.amount_application < self.amount_debit:
                raise Warning('Importe aprobado deber ser menor o igual\na importe solicitado!')
            else:
                if self.partner_id.credit_limit2 == 0.0 and self.amount_debit <= self._credit_max_approved_user(self.partner_id):
                    self.partner_id.status_credit = "active"
                elif not self.partner_id.credit_limit2 == 0.0:
                    raise Warning('El cliente ya tiene linea de crédito asignado,\nsi desea ampliar, seleccione ampliación!')
                elif not self.amount_debit <= self._credit_max_approved_user(self.partner_id):
                    currency_symbol = self.currency_id.symbol
                    raise Warning((u'Ud. puede aprobar sólo hasta: %s %s') % (currency_symbol, self._credit_max_approved_user(self.partner_id)))
            return True
        elif self.process_type == 'extension_request':
            self._not_approve_currency_diff()
            self._amount_debit_zero()

            if self.partner_id.status_credit == "suspension":
                raise Warning('La linea de crédito está suspendido!\nno podrá actualizar, use el tipo Levantar suspensión.')

            if self.amount_application < self.amount_debit:
                raise Warning('Importe aprobado deber ser menor o igual\na importe solicitado!')
            else:
                if self.partner_id.credit_limit2 > 0.0 and (self.partner_id.credit_limit2 + self.amount_debit) <= self._credit_max_approved_user(self.partner_id):
                    self.partner_id.status_credit = "active"
                elif not self.partner_id.credit_limit2 > 0.0:
                    raise Warning('Linea de crédito está en cero,\nseleccione apertura de linea de credito!')
                elif not(self.partner_id.credit_limit2 + self.amount_debit) <= self._credit_max_approved_user(self.partner_id):
                    currency_symbol = self.currency_id.symbol
                    raise Warning((u'supera el monto autorizado a Ud.: %s %s') % (currency_symbol, self._credit_max_approved_user(self.partner_id)))
            return True
        elif self.process_type == 'suspension':
            self._not_approve_currency_diff()
            self.partner_id.status_credit = "suspension"
            return True
        elif self.process_type == 'lift_suspension':
            self._not_approve_currency_diff()
            if self.partner_id.status_credit == "suspension":
                self.partner_id.status_credit = "active"
            else:
                raise Warning('El estado de crédito del cliente no esta suspendido!')
            return True
        elif self.process_type == 'annulment':
            self._not_approve_currency_diff()
            if self.partner_id.credit_limit2 == 0.0:
                raise Warning('Linea de crédito está en cero, no puede anularse!')
            else:
                self.partner_id.status_credit = "annulment"
                credit_limit = self.partner_id.credit_limit2
                self.write({"amount_credit": credit_limit})
            return True

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.currency_id = self.partner_id.currency_id.id
        else:
            self.currency_id = False

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        if self.currency_id:
            self.show_currency_id = self.currency_id.id
        else:
            self.show_currency_id = False

class res_user_credit_limit(models.Model):
    _name = "res.user.credit.limit"
    _rec_name = 'user_id'

    def _get_currency_default_config(self):
        currency_id = literal_eval(self.env["ir.config_parameter"].get_param('nanotec_credit_limit.currency_id', 'False'))
        return currency_id

    def _get_currency_config(self):
        currency_id = literal_eval(self.env["ir.config_parameter"].get_param('nanotec_credit_limit.currency_id', 'False'))
        for rec in self:
            rec.currency_id = currency_id

    user_id = fields.Many2one("res.users", string="Usuario", required=True, ondelete="cascade")
    credit_max_approved = fields.Float("Limite aprobación", required=True, help="Tope de linea de crédito a aprobar")
    order_over_rate = fields.Float("% Sobregiro pedidos", required=True, help="% Sobregiro en pedido autorizado")
    currency_id = fields.Many2one("res.currency", string="Moneda", compute='_get_currency_config', default=_get_currency_default_config)

    _sql_constraints = {
         ('credit_user_id_uniq', 'unique (user_id)',
            'The user must be unique!'),
    }


class credit_detail_bank(models.Model):
    _name = "res.partner.credit.detail.bank"
    _rec_name = 'bank_id'

    def _get_operation_type(self):
        return self.env['base.element'].get_as_selection('BANK.OPERATIONS')

    bank_id = fields.Many2one("res.bank", string="Banco", required=True)
    street = fields.Char("Dirección")
    operation_type = fields.Selection(_get_operation_type, "Tipo de operación")
    amount_operation = fields.Float("Monto de la operación")
    operating_balance = fields.Float("Saldo de operación")
    credit_limit = fields.Float("Limite de crédito")
    start_date = fields.Date("Fecha de inicio")
    phone_contac = fields.Char("Telef. Contacto")
    notes = fields.Text("Notas")
    credit_detail_id = fields.Many2one("res.partner.credit.detail")


class credit_detail_commercial(models.Model):
    _name = "res.partner.credit.detail.commercial"
    _rec_name = 'partner_id'

    partner_id = fields.Many2one("res.partner", string="Empresa", required=True)
    street = fields.Char("Dirección")
    credit_limit = fields.Float("Limite de crédito")
    credit_balance = fields.Float("Saldo de crédito")
    start_date = fields.Date("Fecha de inicio")
    phone_contac = fields.Char("Telef. Contacto")
    notes = fields.Text("Notas")
    credit_detail_id = fields.Many2one("res.partner.credit.detail")


class credit_detail_finantial(models.Model):
    _name = "res.partner.credit.detail.finantial"

    amount_total_assets = fields.Float("Activo Total")
    amount_total_liabilities = fields.Char("Pasivo Total")
    amount_entry = fields.Float("Ingresos")
    status_failure = fields.Boolean("Estado fracaso", help="Algún funcionario o subsidiaria se declaró alguna vez en quiebra?")
    start_date = fields.Date("Fecha de inicio")
    phone_contac = fields.Char("Telef. Contacto")
    notes = fields.Text("Notas")
    credit_detail_id = fields.Many2one("res.partner.credit.detail")
