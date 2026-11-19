# -*- coding: utf-8 -*-

from odoo import models, fields

class MainParameter(models.Model):
    _inherit = 'main.parameter'
    _description = 'Detraction Limit Line'
    
    p_retention = fields.Float(string='Retention percentage', digits=(12, 3))
    min_amount = fields.Float(string='Monto Minimo')

    defaul_detracionts  = fields.Many2one(comodel_name='einvoice.catalog.51', string='Tipo de Operacion por defecto')
    defaul_detraction_payment_id = fields.Many2one(comodel_name='einvoice.catalog.payment', string='Medio de Pago por Defecto')
    

    auto_detractions_clients = fields.Boolean(string='Detracciones Automaticas Clientes', default=False)
    auto_detractions_suppliers = fields.Boolean(string='Detracciones Automaticas Proveedores', default=False)
    round_detractions = fields.Integer(string='Numero de Decimales', default=0)
    partner_cash_id = fields.Many2one('res.partner', string='Partner Caja', help='Partner de Caja que se utilizara por defecto en pagos multiples advance')
    detraction_doc_ids = fields.Many2many('einvoice.catalog.01', 'catalog_01_main_parameter_rel', string='Documentos Afectos a Detraccion')
    limit_line_ids = fields.One2many('detraction.limit.line', 'main_parameter_id')
    round_journal_id = fields.Many2one('account.journal', string='Diario para Redondeo')

class DetractionLimitLine(models.Model):
    _name = 'detraction.limit.line'
    _description = 'Detraction Limit Line'
    
    main_parameter_id = fields.Many2one('main.parameter')
    amount = fields.Float(string='Monto Limite')
    catalog_54_ids = fields.Many2many('einvoice.catalog.54', 'catalog_54_detraction_limit_line_rel', string='Vienes y Servicios Afectos')