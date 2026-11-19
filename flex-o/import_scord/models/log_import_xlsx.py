# -*- coding: utf-8 -*-

from odoo import  fields, models

class LogImportXlsx(models.TransientModel):
    _name = "log.import.xlsx"
    _description = "Model para logs al importar excel"

    name = fields.Char("Nombre Error")
    date = fields.Date("Fecha de actualizacion", default=fields.Date.today())
    description = fields.Char("Descripción")
    ref = fields.Char("Nro Documento")
    file = fields.Char("File")