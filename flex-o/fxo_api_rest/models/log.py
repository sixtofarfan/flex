import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ApiLogsRequest(models.Model):
    _description = "Error log"
    _name = 'api.logs.request'
    _inherit = ['mail.thread']


    name = fields.Char(string="Name", required=False, track_visibility='always')
    web_service = fields.Char(string="WebService", track_visibility='always')
    codigo = fields.Char(string='codigo')
    

    fecha_operacion = fields.Datetime(string="fechaOperacion", default= fields.Datetime.now() ,track_visibility='always')
    tipo_solicitud = fields.Char(string="Tipo de Solicitud", track_visibility='always')
    modelo = fields.Char(string="Modelo", track_visibility='always')

    json_in = fields.Text(string="Json IN", track_visibility='always')
    json_out = fields.Text(string="Json OUT", track_visibility='always')
    error_details = fields.Char(string="Error details", track_visibility='always')

    company_id = fields.Many2one('res.company', string="Company",  default=lambda self: self.env.user.company_id,index=True)
    state = fields.Selection([('new', 'Nuevo'), ('done', 'Ejecutado'), ('error', 'Error')], default='new')