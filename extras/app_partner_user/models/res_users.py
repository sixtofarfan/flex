# -*- coding: utf-8 -*-

from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)

class User(models.Model):
    _inherit = ['res.users']

    is_portal = fields.Boolean(compute='_compute_is_portal', compute_sudo=True, string='Portal User', store=True,)

    @api.model_create_multi
    def create(self, vals_list):
        users = super(User, self).create(vals_list)

        for user in users:
            user.partner_id.write({
                'is_user': True,
                'related_user_id': user.id,
            })
        return users

    def write(self, vals):
        if vals.get('partner_id'):
            for rec in self:
                # 先清旧的
                partner = self.env['res.parnter'].browse(rec.partner_id.id)
                partner.write({
                    'is_user': False,
                    'related_user_id': False,
                })
                # 再更新新的
                partner = self.env['res.parnter'].browse(vals['partner_id'])
                partner.write({
                    'is_user': True,
                    'related_user_id': rec.id,
                })
        return super(User, self).write(vals)

    def unlink(self):
        # 自动删除关联伙伴
        for rec in self:
            ids = []
            ids.append(rec.partner_id.id)
        res = super(User, self).unlink()
        try:
            self.env['res.partner'].browse(ids).unlink()
        except Exception as e:
            _logger.error('remove partner error: %s', e)
        return res

    @api.depends('groups_id')
    def _compute_is_portal(self):
        for user in self:
            user.is_portal = user.has_group('base.group_portal')
