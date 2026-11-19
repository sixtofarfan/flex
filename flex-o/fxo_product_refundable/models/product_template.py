# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    account_refundable_nc_id = fields.Many2one('account.account', string='Cuenta de Reembolso M. N.')
    account_refundable_fc_id = fields.Many2one('account.account', string='Cuenta de Reembolso M. E.')
    account_destination_nc_id = fields.Many2one('account.account', string='Cuenta de Destino M. N.', help='Cuenta para determinar destinos en los pagos')
    account_destination_fc_id = fields.Many2one('account.account', string='Cuenta de Destino M. E.', help='Cuenta para determinar destinos en los pagos')