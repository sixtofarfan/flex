# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleSubscriptionLineState(models.Model):
    _name = 'sale.subscription.line.state'
    _description = 'Sale Subscription Line State'

    name = fields.Char(string='Nombre', default='/', required=True, readonly=True)
    notes = fields.Text(string='Observaciones', states={'done': [('readonly', True)]})
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, states={'done': [('readonly', True)]})
    subscription_id = fields.Many2one('sale.subscription', string='Contrato', required=True,
                                      states={'done': [('readonly', True)]})
    subscription_line_id = fields.Many2one('sale.subscription.line', string='Item del Contrato', required=True,
                                           states={'done': [('readonly', True)]})
    product_line = fields.Many2one('product.product', related='subscription_line_id.product_id', string='Producto')
    street_line = fields.Many2one('res.partner', related='subscription_line_id.partner_street_destination',
                                  string='Direccion')
    state_line = fields.Selection(related='subscription_line_id.state', string='Estado actual del Item', required=True)
    historical_state = fields.Selection([
        ('done', 'Activo'),
        ('suspend', 'Suspendido'),
        ('pending', 'Pendiente'),
        ('cancel', 'Baja'),
    ], readonly=True, string='Estado al que se cambio el Item')
    date = fields.Datetime(string='Fecha de Actualizacion', default=fields.Datetime.now(), required=True,
                           states={'done': [('readonly', True)]})
    user_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user.id, required=True,
                              readonly=True, states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Finalizado'),
    ], string='Estado', default='draft')
    stop_date = fields.Date(string='Previous Stop Date', readonly=True, states={'done': [('readonly', True)]})

    @api.onchange('subscription_line_id')
    def _onchange_subscription_line_id(self):
        self.stop_date = self.subscription_line_id.stop_date

    def set_draft(self):
        self.state = 'draft'
        self.name = '/'

    def set_confirm(self):
        self.state = 'confirmed'
        self.name = self.env['ir.sequence'].next_by_code('sale_subs_line_state') or '/'

    def set_done(self):
        self.state = 'done'
        self.subscription_line_id.state = self.historical_state
        self.subscription_line_id.stop_date = self.date

    def finish_line(self):
        self.historical_state = 'done'

    def suspend_line(self):
        self.historical_state = 'suspend'

    def cancel_line(self):
        self.historical_state = 'cancel'
