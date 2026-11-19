import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

import xmlrpc.client
import json,ssl

class ResCompany(models.Model):
    _inherit = 'res.company'

    param_url_cablego = fields.Char(string=u'URL Conexion', help='https://odoo.flx.com.pe or http://odoo.flx.com.pe')
    param_db_cablego = fields.Char(string=u'Base de datos')
    param_username_cablego = fields.Char(string=u'Usuario')
    param_password_cablego = fields.Char(string=u'Clave')
