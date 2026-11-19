# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError

class CrmTeam(models.Model):

    _inherit = "crm.team"

    approval2_ids = fields.Many2many('approval.category','approval2_ids','id_crm_team', string='Aprobadores Cliente Declarado')


class RequestTemRouter(models.Model):
    _name = 'crm.team.router.request'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']
    
    def _defaul_user(self):
        return self.env.user.id

    name = fields.Char(string='Numero de Documento', default="New",tracking=True)
    user_id = fields.Many2one(comodel_name='res.users', string='User', default=_defaul_user)
    
    partner_id = fields.Many2one(comodel_name='res.partner', string='Client',tracking=True)
    description = fields.Text(string='Descripcion de la Solicitud',tracking=True)
    
    date_request = fields.Date(default=fields.Date.today(),string='Fecha de Solicitud',tracking=True)
    date_due = fields.Date(default=fields.Date.today(),string='Fecha de vencimiento',tracking=True)
    
    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('done', 'Done'),
        ],default='draft',tracking=True)

    approval_id = fields.One2many(comodel_name='approval.request',
                                  inverse_name='permanence_id',
                                  string='Aprovate',tracking=True)
    
    

    def update_state(self):
        temp = 'done'
        error = True
        for item in self.approval_id:
            if item.request_status == 'refused' or item.request_status ==  'cancel':
                self.state = 'canceled'
                error= False
                break
            elif item.request_status == 'new' or item.request_status ==  'pending':
                self.state = 'confirmed'
                error= False
                break
        if error:
            self.state = temp

    @api.constrains('name')
    def agergar_secuencia(self):
        if self.name == "New":
            self.name = self.env['ir.sequence'].next_by_code('crm.team.router.request')
    

    def unlink(self):
        for request in self:
            if request.state in ['confirmed', 'canceled', 'done']:
                raise UserError(_('You cannot delete a document that is in %s state.') % _(request.state,))
        return super(RequestTemRouter, self).unlink()

    def set_draft(self):
        for item in self.approval_id:
            item.unlink()

    def confirm(self):
        search = self.env['approval.request'].search([(
            'permanence_id','=', self.ids[0]
        )])
        for elemt in search:
            elemt.action_cancel()
            elemt.unlink()
        
        for item in self.env.user.sale_team_id.approval2_ids:
            data = {
                'name': str(self.name + "-" + item.name),
                'category_id': item.id,
                'partner_id': self.partner_id.id,
                'request_owner_id': self.env.user.id,
                'reference': str(self.name),
                'permanence_id': self.ids[0]
            }
            temp = self.env['approval.request'].create(data)

            for user in item.user_ids:
                self.env['approval.approver'].create({
                    'user_id': user.id,
                    'request_id': temp.id,
                })
            temp.action_confirm()
        self.state = 'confirmed'