# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class DatosServer(models.Model):
    _name = "sync.data.server"

    name = fields.Char("name", required=True)
    usuario = fields.Char('Usuario', required=True)
    password = fields.Char('Password', required=True)
    puerto = fields.Char("Port", required=True)
    nombre_servicio = fields.Char("Nombre de servicio", required=True)
    servidor = fields.Char("Servidor", required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False)
    active = fields.Boolean("Active", default=True)

  
    def action_draft(self):
        self.state = "draft"

    
    def action_done(self):
        self.state = "done"

  
    def action_cancel(self):
        self.state = "cancel"