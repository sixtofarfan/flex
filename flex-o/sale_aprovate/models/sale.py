# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import UserError


class CrmTeam(models.Model):

    _inherit = "crm.team"
    level_id = fields.One2many(comodel_name='crm.team.level',
                                inverse_name='team_id',
                                string='Level')

class CrmTeamLevel(models.Model):
    _name = 'crm.team.level'

    name    = fields.Char(string="Level")
    team_id = fields.Many2one(comodel_name='crm.team', string='Team')
    users_id = fields.Many2many(comodel_name='res.users', string='User')

class SaleOrdeLevel(models.Model):

    _name = 'sale.team.level'

    name = fields.Selection(string='State',
                            selection=[
                                ('approved', 'Approved'),
                                ('draft', 'Draft'),
                            ],
                            default="draft")
    level_id = fields.Many2one(comodel_name='crm.team.level', string='Level')
    sale_id = fields.Many2one(comodel_name='sale.order', string='Order')

    @api.onchange('name')
    def onchange_name(self):
        if not self.env.user.id in self.level_id.users_id.ids:
            self.name = 'draft'
            raise UserError(_('No Tienes Autorizacion'))

class Sale(models.Model):
    _inherit = "sale.order"

    level_ids = fields.One2many(comodel_name='sale.team.level',
                                inverse_name='sale_id',
                                string='Aprovate')
    @api.onchange('team_id')
    def onchange_team_id(self):
        self.create_level_ids()

    @api.model
    def create_level_ids(self):
        search = self.env['sale.team.level'].search([(
            'sale_id','=', self.ids[0]
        )])
        for elemt in search:
            elemt.unlink()

        for item in self.team_id.level_id:
            data = {
                'name': 'draft',
                'level_id':item.id,
                'sale_id': self.ids[0]
                }
            self.env['sale.team.level'].create(data)

    def action_confirm(self):
        for item in self.level_ids:
            if item.name == 'draft':
                raise UserError(_('Falta autorizar ' + str(item.level_id.name)))
        super(Sale, self).action_confirm()