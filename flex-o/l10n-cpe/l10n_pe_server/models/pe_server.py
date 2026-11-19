# -*- coding: utf-8 -*-
from odoo import models, fields, api


class pe_sunat_server(models.Model):
    _name = 'pe.server'
    _description = 'Peruvian Server'

    name = fields.Char("Name", required=True)
    url = fields.Char("Url", required=True)
    user = fields.Char("User")
    password = fields.Char("Password")
    description = fields.Text("Description")
    active = fields.Boolean("Active", default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    id_sunat = fields.Char(string='Id Sunat')
    clave_sunat = fields.Char(string='Clave Sunat')
    url_token = fields.Char(string='Url generar Token',default="https://api-seguridad.sunat.gob.pe/v1/clientessol/%s/oauth2/token/")
    scope = fields.Char(string='Scope', default='https://api-cpe.sunat.gob.pe')
    url_consult = fields.Char(string='Url consultar GRE',default="https://api-cpe.sunat.gob.pe/v1/contribuyente/gem/comprobantes/envios/%s")

    def action_draft(self):
        self.state = "draft"

    def action_done(self):
        self.state = "done"

    def action_cancel(self):
        self.state = "cancel"
