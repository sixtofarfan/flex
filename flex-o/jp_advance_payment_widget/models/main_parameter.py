# -*- coding:utf-8 -*-
from odoo import api, fields, models

class MainParameter(models.Model):
	_inherit = 'main.parameter'

	# supplier_advance_account_receipt_nc = fields.Many2one('account.account', string='Cuenta de Anticipo Recibos M.N.')
	# supplier_advance_account_receipt_fc = fields.Many2one('account.account', string='Cuenta de Anticipo Recibos M.E.')
	other_accounts_client = fields.One2many('account.account', 'main_parameter_id_client', string='Other accounts to apply Customer')
	other_accounts_supplier = fields.One2many('account.account', 'main_parameter_id_supplier', string='Other accounts to apply Suppliers')
	# field_name = fields.One2many('comodel_name', 'inverse_field_name', string='')
	# other_accounts_client = fields.Many2one('account.account', string='Otras cuentas por aplicar Clientes')
	# other_accounts_supplier = fields.Many2one('account.account', string='Otras cuentas por aplicar Proveedores')

class AccountAccount(models.Model):
    _inherit = 'account.account'

    main_parameter_id_client = fields.Many2one('main.parameter', string='Main Parameters')
    main_parameter_id_supplier = fields.Many2one('main.parameter', string='Main Parameters')
    