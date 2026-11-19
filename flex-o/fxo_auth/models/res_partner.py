# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    aname    = fields.Char(string='Name')
    las_name = fields.Char(string='Last name')
    ruc  = fields.Char(string='')
    trabajadores  = fields.Integer(string='Trabajadores')
    alumnos_menores  = fields.Integer(string='Alumnos Menores')
    alumnos_mayores  = fields.Integer(string='Alumnos Maryores')    
    email_institucional   = fields.Char(string='Email Institucional')    
    cargo  = fields.Char(string='Cargo')    
    nombre_responsable  = fields.Char(string='Nombre')
    apellido_responsable  = fields.Char(string='Apellido')

    birthday = fields.Date('Date of Birth')
    sex = fields.Selection(string='Sex', selection=[('1', 'Masculino'), ('2', 'Femenino'),])
    nro_registro = fields.Char(
        string='N° de registro de usuario', default="New")


    @api.constrains('nro_registro')
    def agergar_secuencia(self):
        if self.nro_registro == "New":
            #self.nro_registro = self.env['ir.sequence'].next_by_code('res.partner.registro')
            self.env.cr.execute("""
            select count(*) +  sum(trabajadores) + sum(alumnos_menores)  +  sum(alumnos_mayores) as cant from res_partner
			""")
            query = self.env.cr.fetchall()
            temp = 0 
            for p in query:
                temp = p[0]
            self.nro_registro = temp
            