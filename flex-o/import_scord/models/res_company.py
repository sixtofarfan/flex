
from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    param_url_scord = fields.Char(string=u'URL Conexión', help='https://odoo.flx.com.pe or http://odoo.flx.com.pe')
    param_db_scord = fields.Char(string=u'Base de datos')
    param_username_scord = fields.Char(string=u'Usuario')
    param_password_scord = fields.Char(string=u'Clave')

    param_ftp_server = fields.Char(string=u'Ftp Conexión')
    param_ftp_username = fields.Char(string=u'Ftp Usuario')
    param_ftp_password = fields.Char(string=u'Ftp Contraseña')

    category_product_id = fields.Char(string=u'Categoria Producto')
    account_journal_id = fields.Char(string=u'Diario')
    account_company_id = fields.Char(string=u'Compañia')
    taxes_id = fields.Char(string=u'Impuesto')