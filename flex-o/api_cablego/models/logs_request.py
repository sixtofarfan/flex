import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError


class LogsRequest(models.Model):
    _description = "Error log"
    _name = 'logs.request.cablego'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=False,
                       track_visibility='always')
    email = fields.Char(string='Email')
    
    web_service = fields.Char(string="WebService", track_visibility='always')
    referencia_deuda = fields.Char(string="Socio", track_visibility='always')
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.user.company_id, index=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Patrner')

    json_in = fields.Text(string="Json IN", track_visibility='always')
    json_out = fields.Text(string="Json OUT", track_visibility='always')
    error_details = fields.Char(
        string="Error details", track_visibility='always')

    stages_id = fields.Selection(
        [('new', 'Nuevo'), ('done', 'Ejecutado'), ('error', 'Error')], default='new')
