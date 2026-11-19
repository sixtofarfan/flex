# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date


class SaleSubscriptionSuspendReactivated(models.Model):
    _name = 'sale.subscription.suspend.reactivated'

    @api.model
    def _default_request_date(self):
        return date.today()

    name = fields.Char(string='Request Number', default='/', required=True, readonly=True)
    observations = fields.Text(string='Observations',
                               states={'done': [('readonly', True)], 'confirmed': [('readonly', True)]})
    type = fields.Selection(selection=[('suspension', 'Suspension'), ('reactivation', 'Reactivation')], string='Type',
                            required=True, default='suspension',
                            states={'done': [('readonly', True)], 'confirmed': [('readonly', True)]})
    request_date = fields.Date(string='Request Date', readonly=True, default=_default_request_date)
    request_user_id = fields.Many2one('res.users', string='Request User', default=lambda self: self.env.user.id,
                                      readonly=True)
    confirmed_date = fields.Date(string='Confirmed Date', readonly=True)
    confirmed_user_id = fields.Many2one('res.users', string='Confirmed User', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id,
                                 readonly=True)
    subscription_ids = fields.Many2many('sale.subscription', 'sale_subscription_stage_suspend_reactivated_rel',
                                        'subscription_id', 'stage_sr_id', string='Subscriptions',
                                        states={'done': [('readonly', True)], 'confirmed': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('done', 'Realizado'),
    ], string='Estado', default='draft')

    def set_draft(self):
        self.state = 'draft'
        self.name = '/'

    def set_confirm(self):
        self.state = 'confirmed'
        if self.type == 'suspension':
            self.name = self.env['ir.sequence'].next_by_code('sale_subscription_state_suspend') or '/'
        else:
            self.name = self.env['ir.sequence'].next_by_code('sale_subscription_state_reactivated') or '/'

    def set_done(self):
        #if self.env.user.id == self.request_user_id.id:
        #    raise ValidationError("El usuario que aprueba no puede ser el mismo que solicita.")
        if self.request_date > date.today():
            raise ValidationError("La fecha de confirmación no puede ser menor que la fecha de solicitud.")
        if len(self.subscription_ids) == 0:
            raise ValidationError("Debe seleccionar al menos un contrato.")
        self.state = 'done'
        self.confirmed_date = date.today()
        self.confirmed_user_id = self.env.user.id
        for sub in self.subscription_ids:
            if self.type == 'suspension':
                sale_subscription_stage = self.env['sale.subscription.stage'].search([('name', '=', 'Suspendido')])
            else:
                sale_subscription_stage = self.env['sale.subscription.stage'].search([('in_progress', '=', True)])
            sub.stage_id = sale_subscription_stage.id

    def unlink(self):
        for res in self:
            if res.state == 'done':
                raise ValidationError("No puede eliminar una solicitud ya aprobada." + res.name)
        return super(SaleSubscriptionSuspendReactivated, res).unlink()

    @api.onchange('type')
    def _onchange_type(self):
        sale_subscription = self.env['sale.subscription']
        domain = list()
        if self.type:
            if self.type == 'suspension':
                domain.append(('stage_id.in_progress', '=', True))
                sale_subscription_ids = sale_subscription.search(domain)
                return {'domain': {'subscription_ids': [('id', 'in', sale_subscription_ids.ids)]}}
            else:
                domain.append(('stage_id.name', '=', 'Suspendido'))
                sale_subscription_ids = sale_subscription.search(domain)
                return {'domain': {'subscription_ids': [('id', 'in', sale_subscription_ids.ids)]}}


class SaleSubscription(models.Model):
    _inherit = 'sale.subscription'

    stage_suspend_reactivated_ids = fields.Many2many('sale.subscription.suspend.reactivated',
                                                     'sale_subscription_stage_suspend_reactivated_rel',
                                                     'stage_sr_id', 'subscription_id',
                                                     string='Historial de suspensiones y reactivaciones',
                                                     domain="[('state', '=', 'done')]")
