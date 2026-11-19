# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    #Facturación Electrónica
    pe_certificate = fields.Many2one('pe.certificate', string='Company Certificate', 
                                     domain="[('state','=','done')]")
    pe_server = fields.Many2one('pe.server', string='Company Server', 
                                     domain="[('state','=','done')]")
    pe_is_sync = fields.Boolean("Is Synchronous", default= True)
    sunat_resolution_type = fields.Char("Resolution Type")
    sunat_resolution_number = fields.Char("Resolution Number")
    pe_branch_code = fields.Char("Branch Code", default="0000")

    #Detracciones
    module_jp_account_invoice_detraction = fields.Boolean(string='Use detractions on invoices')
    sunat_amount = fields.Float(string="Minimum Detraction Amount", digits=(16,2))
    det_percent_by = fields.Selection([
        ('1', 'By Product'),
        ('2', 'By Partner'),
        ('3', 'Fixed')
    ], string='Detraction percent method', related='company_id.det_percent_by', readonly=False)
    det_percent = fields.Float(string="Detraction Percent", digits=(16,2), default=12.0, required=True)
    type_operation = fields.Many2one('type.operation', string='Type of Operation')
    type_good_service = fields.Many2one('good.service', string='Goods and Services')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        module_jp_account_invoice_detraction = params.get_param('l10n_pe_cpe.module_jp_account_invoice_detraction')
        pe_certificate_id = int(params.get_param('l10n_pe_cpe.pe_certificate'))
        pe_server_id = int(params.get_param('l10n_pe_cpe.pe_server'))
        sunat_amount = float(params.get_param('l10n_pe_cpe.sunat_amount'))
        sunat_resolution_type = params.get_param('l10n_pe_cpe.sunat_resolution_type')
        sunat_resolution_number = params.get_param('l10n_pe_cpe.sunat_resolution_number')
        # det_percent_by = params.get_param('l10n_pe_cpe.det_percent_by')
        det_percent = float(params.get_param('l10n_pe_cpe.det_percent'))
        type_operation = int(params.get_param('l10n_pe_cpe.type_operation'))
        type_good_service = int(params.get_param('l10n_pe_cpe.type_good_service'))
        print(params.get_param('l10n_pe_cpe.pe_certificate'))
        # print(params.get_param('l10n_pe_cpe.type_operation'))
        res.update(
            module_jp_account_invoice_detraction = module_jp_account_invoice_detraction,
            pe_certificate = pe_certificate_id,
            pe_server = pe_server_id,
            sunat_amount = sunat_amount,
            sunat_resolution_type = sunat_resolution_type,
            sunat_resolution_number = sunat_resolution_number,
            # det_percent_by = det_percent_by,
            det_percent = det_percent,
            type_operation = type_operation,
            type_good_service = type_good_service,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.module_jp_account_invoice_detraction",
            self.module_jp_account_invoice_detraction)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.pe_certificate",
            self.pe_certificate.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.pe_server",
            self.pe_server.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.sunat_amount",
            self.sunat_amount)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.sunat_resolution_type",
            self.sunat_resolution_type)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.sunat_resolution_number",
            self.sunat_resolution_number)
        # self.env['ir.config_parameter'].sudo().set_param(
        #     "l10n_pe_cpe.det_percent_by",
        #     self.det_percent_by)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.det_percent",
            self.det_percent)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.type_operation",
            self.type_operation.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "l10n_pe_cpe.type_good_service",
            self.type_good_service.id)