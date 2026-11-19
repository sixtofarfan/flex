from odoo import fields, models, api, _
import json
from datetime import *

import requests
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    collection_id = fields.Many2one('res.users', string='Cobrador')
    # Este campo usa api_power_bi, pero causa lentitud y problemas en la compilacion.
    # cancelation_date = fields.Date(compute='_get_cancelation_move_date', store=True, string='Fecha de Cancelacion')
    invoice_period_id = fields.Many2one('account.period', string='Periodo de Facturacion')

    # @api.depends('invoice_payments_widget')
    # def _get_cancelation_move_date(self):
    #    for rec in self:
    #        if rec.invoice_payments_widget:
    #            dates = []
    #            parse_dict = json.loads(rec.invoice_payments_widget)
    #            if parse_dict:
    #                for pay in parse_dict.get('content'):
    #                    dates.append(datetime.strptime(pay.get('date'), '%Y-%m-%d').date())
    #                rec.cancelation_date = max(dates)
    #            else:
    #                rec.cancelation_date = None	
    #        else:
    #            rec.cancelation_date = None

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        MainParameter = self.env['main.parameter'].search([('company_id', '=', self.env.company.id)], limit=1)
        if not MainParameter.use_invoice_period:
            res.invoice_period_id = None
        return res
