# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_new_starting_point(self):
        if self.picking_type_id.code == 'incoming': 
            return self.partner_id
        elif self.picking_type_id.code == 'outgoing':
            return self.env.company.partner_id
    
    def _get_new_ending_point(self):
        if self.picking_type_id.code == 'incoming': 
            return self.env.company.partner_id
        elif self.picking_type_id.code == 'outgoing':
            return self.partner_id

    new_starting_point = fields.Many2one(
        'res.partner', string='Starting point',required=True,
        # states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)], 'assigned': [('readonly', False)]},
        # domain="['|', ('company_id', '=', False), ('parent_id', '=', partner_id)]",
        default=_get_new_starting_point)
    new_ending_point = fields.Many2one(
        'res.partner', string='Ending point',required=True,
        # states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)], 'assigned': [('readonly', False)]},
        # domain="[('parent_id', '=', partner_id)]",
        default=_get_new_ending_point)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.picking_type_id.code == 'incoming':
            self.new_starting_point = self.partner_id
            # self.starting_point = self.new_starting_point.street
            self.new_ending_point = self.env.company.partner_id
            # self.ending_point = self.new_ending_point.street
        elif self.picking_type_id.code == 'outgoing':
            self.new_starting_point = self.env.company.partner_id
            # self.starting_point = self.new_starting_point.street
            self.new_ending_point = self.partner_id if self.partner_id else self.env.company.partner_id
            # self.ending_point = self.new_ending_point.street
        domain = {}
        domain_company_start = {}
        domain_company_end = {}
        domain_partner_start = {}
        domain_partner_end = {}
        if any(child.type == 'delivery' for child in self.env.company.partner_id.child_ids):
            domain_company_start['new_starting_point'] = [('parent_id', '=', self.env.company.partner_id.id), ('type','=','delivery')]
            domain_company_end['new_ending_point']     = [('parent_id', '=', self.env.company.partner_id.id), ('type','=','delivery')]
        else:
            domain_company_start['new_starting_point'] = [('id', '=', self.env.company.partner_id.id)]
            domain_company_end['new_ending_point']     = [('id', '=', self.env.company.partner_id.id)]
        if any(child.type == 'delivery' for child in self.partner_id.child_ids):
            domain_partner_start = {'new_starting_point': [('parent_id', '=', self.partner_id.id), ('type','=','delivery')],}
            domain_partner_end   = {'new_ending_point'  : [('parent_id', '=', self.partner_id.id), ('type','=','delivery')],}
        else:
            if self.partner_id:
                domain_partner_start = {'new_starting_point': [('id', '=', self.partner_id.id)],}
                domain_partner_end   = {'new_ending_point'  : [('id', '=', self.partner_id.id)],}
            else:
                domain_partner_start = domain_company_start
                domain_partner_end   = domain_company_end
        if self.picking_type_id.code == 'internal':
            domain_company_start.update(domain_company_end)
            domain['domain'] = domain_company_start
        elif self.picking_type_id.code == 'incoming':
            domain_partner_start.update(domain_company_end)
            domain['domain'] = domain_partner_start
        elif self.picking_type_id.code == 'outgoing':
            domain_company_start.update(domain_partner_end)
            domain['domain'] = domain_company_start
        return domain

    @api.model
    def create(self, vals):
        pt = self.env['stock.picking.type'].search([('id', '=', vals['picking_type_id'])])
        if pt.code == 'incoming':
            vals['new_starting_point'] =  vals['partner_id'] if vals['partner_id'] else vals['new_starting_point']
            vals['new_ending_point']   =  self.env.company.partner_id.id
        elif pt.code == 'outgoing':
            vals['new_starting_point'] = self.env.company.partner_id.id
            if vals['origin']:
                sale_id = self.env['sale.order'].search([('name','=', vals['origin'])])
                vals['new_ending_point'] =  sale_id.partner_shipping_id.id if sale_id else vals['new_ending_point']
            else:
                vals['new_ending_point'] =  vals['partner_id'] if vals['partner_id'] else vals['new_ending_point']
        return super(StockPicking,self).create(vals)

    @api.onchange('new_starting_point')
    def _onchange_new_starting_point(self):
        self.starting_point = self.new_starting_point.street # if self.new_starting_point.street else self.partner_id.street
        
    @api.onchange('new_ending_point')
    def _onchange_new_ending_point(self):
        self.ending_point = self.new_ending_point.street # if self.new_ending_point.street else self.partner_id.street

    """ Funcion escondida para aplicar las direcciones a los campos escondidos
        luego de instalar este modulo. Se hace creando una accion planificada
        en automatizacion. model._update_ending_point()"""
    def _update_ending_point(self):
        pickings = self.env['stock.picking'].search([])
        for p in pickings:
            if p.origin:
                sale_id = p.env['sale.order'].search([('name','=', p.origin)])
                p.new_ending_point =  sale_id.partner_shipping_id
                p.ending_point = p.new_ending_point.street
            else:
                p.new_ending_point =  p.partner_id
                p.ending_point = p.partner_id.street