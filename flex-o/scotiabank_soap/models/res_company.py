import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

import xmlrpc.client
import json,ssl

class ResCompany(models.Model):
    _inherit = 'res.company'

    stb_param_url = fields.Char(string=u'URL Conexion', help='https://odoo.flx.com.pe or http://odoo.flx.com.pe')
    stb_param_db = fields.Char(string=u'Base de datos')
    stb_param_username = fields.Char(string=u'Usuario')
    stb_param_password = fields.Char(string=u'Clave')

    #Datos de Monedas USD y PEN ODOO
    stb_param_currency_usd = fields.Integer(string=u'ID Moneda USD')
    stb_param_currency_pen = fields.Integer(string=u'ID Moneda PEN')

    #Datos del Diario USD ODOO
    stb_param_journal_usd = fields.Integer(string=u'ID Diario USD')
    stb_journal_usd_name = fields.Char(string=u'Nombre Diario USD')

    #Datos del Diario PEN ODOO
    stb_param_journal_pen = fields.Integer(string=u'ID Diario PEN')
    stb_journal_pen_name = fields.Char(string=u'Nombre Diario PEN')

    #Datos del Cuenta USD ODOO
    stb_param_account_usd = fields.Integer(string=u'ID Cuenta USD')
    stb_account_usd_name = fields.Char(string=u'Nombre Cuenta USD')

    #Datos del Cuenta PEN ODOO
    stb_param_account_pen = fields.Integer(string=u'ID Cuenta PEN')
    stb_account_pen_name = fields.Char(string=u'Nombre Cuenta PEN')

    #Datos de Contratos BBVA
    stb_contract_usd = fields.Char(string=u'Codigo Servicio USD')
    stb_contract_pen = fields.Char(string=u'Codigo Servicio PEN')
