import datetime
import logging
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.exceptions import UserError

import xmlrpc.client
import json,ssl

class ResCompany(models.Model):
    _inherit = 'res.company'

    param_url = fields.Char(string=u'URL Conexion', help='https://odoo.flx.com.pe or http://odoo.flx.com.pe')
    param_db = fields.Char(string=u'Base de datos')
    param_username = fields.Char(string=u'Usuario')
    param_password = fields.Char(string=u'Clave')

    #Datos de Monedas USD y PEN ODOO
    param_currency_usd = fields.Integer(string=u'ID Moneda USD')
    param_currency_pen = fields.Integer(string=u'ID Moneda PEN')

    #Datos del Diario USD ODOO
    param_journal_usd = fields.Integer(string=u'ID Diario USD')
    journal_usd_name = fields.Char(string=u'Nombre Diario USD')

    #Datos del Diario PEN ODOO
    param_journal_pen = fields.Integer(string=u'ID Diario PEN')
    journal_pen_name = fields.Char(string=u'Nombre Diario PEN')

    #Datos del Cuenta USD ODOO
    param_account_usd = fields.Integer(string=u'ID Cuenta USD')
    account_usd_name = fields.Char(string=u'Nombre Cuenta USD')

    #Datos del Cuenta PEN ODOO
    param_account_pen = fields.Integer(string=u'ID Cuenta PEN')
    account_pen_name = fields.Char(string=u'Nombre Cuenta PEN')

    #Datos de Contratos BBVA
    bbva_contract_usd = fields.Char(string=u'Codigo Contrato USD')
    bbva_contract_pen = fields.Char(string=u'Codigo Contrato PEN')


    def action_consult_params(self):

            #Conexion con Base de datos...
            common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(self.param_url),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            uid = common.authenticate(self.param_db, self.param_username, self.param_password, {})
            #print (common.version())

            models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.param_url),verbose=False,use_datetime=True,context=ssl._create_unverified_context())
            conex_result = models.execute_kw(self.param_db, uid, self.param_password, 'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

            #Extraer IDs de Monedas
            currency_USD = models.execute_kw(self.param_db, uid, self.param_password,'res.currency', 'search_read', [[['name', '=', 'USD']]],
                {'fields': ['id', 'name'], 'limit': 1})
            self.param_currency_usd = currency_USD[0]['id']

            currency_PEN = models.execute_kw(self.param_db, uid, self.param_password,'res.currency', 'search_read', [[['name', '=', 'PEN']]],
                {'fields': ['id', 'name'], 'limit': 1})
            self.param_currency_pen = currency_PEN[0]['id']


            #Extraer IDs de Journal del banco continental
            journal_USD = models.execute_kw(self.param_db, uid, self.param_password,'account.journal', 'search_read', [[['name', 'ilike', 'BBVA ME']]],
                {'fields': ['id', 'name'], 'limit': 1})
            self.param_journal_usd = journal_USD[0]['id']
            self.journal_usd_name = journal_USD[0]['name']

            journal_PEN = models.execute_kw(self.param_db, uid, self.param_password,'account.journal', 'search_read', [[['name', 'ilike', 'BBVA MN']]],
                {'fields': ['id', 'name'], 'limit': 1})
            self.param_journal_pen = journal_PEN[0]['id']
            self.journal_pen_name = journal_PEN[0]['name']


            #Extraer IDs de Journal del banco continental
            account_USD = models.execute_kw(self.param_db, uid, self.param_password,'currency.parameter.line', 'search_read', [[['currency_id', '=', self.param_currency_usd]]],
                {'fields': ['id','credit_account_id'], 'limit': 1})

            self.param_account_usd = account_USD[0]['credit_account_id'][0]
            self.account_usd_name = account_USD[0]['credit_account_id'][1]

            account_PEN = models.execute_kw(self.param_db, uid, self.param_password,'currency.parameter.line', 'search_read', [[['currency_id', '=', self.param_currency_pen]]],
                {'fields': ['id','credit_account_id'], 'limit': 1})

            self.param_account_pen = account_PEN[0]['credit_account_id'][0]
            self.account_pen_name = account_PEN[0]['credit_account_id'][1]