# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr


_logger = logging.getLogger(__name__)



class Partner(models.Model):
    _inherit = 'res.partner'

    collection_id = fields.Many2one('res.users','Cobrador')
    user2_id = fields.Many2one('res.users','Post-Venta')


class Res_Users(models.Model):
    _inherit = 'res.users'

    sale_collection_qty = fields.Integer('Cantidad por Cobrar',compute="get_sale_collection_qty")

    def get_sale_collection_qty(self):
        for i in self:
            i.sale_collection_qty = len(self.env['res.partner'].search([('collection_id','=',i.id)]))


class Sale_Order(models.Model):
    _inherit = 'sale.order'

    collection_team_id = fields.Many2one('crm.team','Equipo de Cobranza')


    def action_confirm(self):
        t = super(Sale_Order, self).action_confirm()
        for i in self:
            if i.collection_team_id.id and not i.partner_id.collection_id.id:
                if len(i.collection_team_id.member_ids) == 0:
                    pass
                else:
                    menor = i.collection_team_id.member_ids[0]
                    for cob in i.collection_team_id.member_ids:
                        if menor.sale_collection_qty > cob.sale_collection_qty:
                            menor = cob
                    i.partner_id.collection_id = menor.id
        return t
