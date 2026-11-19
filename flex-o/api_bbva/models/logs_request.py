import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError


class LogsRequest(models.Model):
    _description = "Error log"
    _name = 'logs.request'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=False, track_visibility='always')

    web_service = fields.Char(string="WebService", track_visibility='always')
    referencia_deuda = fields.Char(string="Socio", track_visibility='always')
    numero_documento = fields.Char(string="Documento", track_visibility='always')

    codigoOperacion = fields.Char(string="Código Operacion", track_visibility='always')
    numeroOperacion = fields.Char(string="Nro Operacion", track_visibility='always')
    codigoBanco = fields.Char(string="Código Banco", track_visibility='always')
    codigoConvenio = fields.Char(string="Código Convenio", track_visibility='always')
    canalOperacion = fields.Char(string="Canal Operacion", track_visibility='always')
    codigoOficina = fields.Char(string="Código Oficina", track_visibility='always')
    fechaOperacion = fields.Char(string="fechaOperacion", track_visibility='always')
    horaOperacion = fields.Char(string="horaOperacion", track_visibility='always')

    json_in = fields.Text(string="Json IN", track_visibility='always')
    json_out = fields.Text(string="Json OUT", track_visibility='always')
    error_details = fields.Char(string="Error details", track_visibility='always')

    company_id = fields.Many2one('res.company', string="Company",  default=lambda self: self.env.user.company_id,
                                   index=True)
    stages_id = fields.Selection(
        [('new', 'Nuevo'), ('done', 'Ejecutado'), ('error', 'Error')], default='new')
