# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
  
    customer_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Customer Journal for Bills of Exchange', domain="[('company_id', '=', company_id)]", related='company_id.customer_boe_journal_id', readonly=False)
    supplier_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Supplier Journal for Bills of Exchange', domain="[('company_id', '=', company_id)]", related='company_id.supplier_boe_journal_id', readonly=False)
    retention_boe_account_id = fields.Many2one(comodel_name='account.account', string='Retention Account for Bills of Exchange', domain="[('company_id', '=', company_id)]", related='company_id.retention_boe_account_id', readonly=False)
    protests_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Protests Journal', domain="[('company_id', '=', company_id)]", related='company_id.protests_boe_journal_id', readonly=False)
    protests_financial_expenses_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Protests Financial Expenses Journal', domain="[('company_id', '=', company_id)]", related='company_id.protests_financial_expenses_boe_journal_id', readonly=False)
    bank_interests_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Bank Interests Journal', domain="[('company_id', '=', company_id)]", related='company_id.bank_interests_boe_journal_id', readonly=False)
    round_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Round Gain and Loss Journal', domain="[('company_id', '=', company_id)]", related='company_id.round_boe_journal_id', readonly=False)
    bank_claim_journal_id = fields.Many2one(comodel_name='account.journal', string='Bank Interests Claim Journal', domain="[('company_id', '=', company_id)]", related='company_id.bank_claim_journal_id', readonly=False)
    advanced_boe_journal_id = fields.Many2one(comodel_name='account.journal', string='Advanced Journal', domain="[('company_id', '=', company_id)]", related='company_id.advanced_boe_journal_id', readonly=False)
    protests_financial_expenses_boe_account_id = fields.Many2one(comodel_name='account.account', string='Protests Financial Expenses Account', domain="[('company_id', '=', company_id)]", related='company_id.protests_financial_expenses_boe_account_id', readonly=False)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        customer_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.customer_boe_journal_id'))
        supplier_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.supplier_boe_journal_id'))
        retention_boe_account_id = int(params.get_param('jp_account_bills_of_exchange.retention_boe_account_id'))
        protests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_boe_journal_id'))
        protests_financial_expenses_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id'))
        bank_interests_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.bank_interests_boe_journal_id'))
        round_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.round_boe_journal_id'))
        bank_claim_journal_id = int(params.get_param('jp_account_bills_of_exchange.bank_claim_journal_id'))
        advanced_boe_journal_id = int(params.get_param('jp_account_bills_of_exchange.advanced_boe_journal_id'))
        protests_financial_expenses_boe_account_id = int(params.get_param('jp_account_bills_of_exchange.protests_financial_expenses_boe_account_id'))
        res.update(
            customer_boe_journal_id = customer_boe_journal_id,
            supplier_boe_journal_id = supplier_boe_journal_id,
            retention_boe_account_id = retention_boe_account_id,
            protests_boe_journal_id = protests_boe_journal_id,
            protests_financial_expenses_boe_journal_id = protests_financial_expenses_boe_journal_id,
            bank_interests_boe_journal_id = bank_interests_boe_journal_id,
            round_boe_journal_id = round_boe_journal_id,
            bank_claim_journal_id = bank_claim_journal_id,
            advanced_boe_journal_id = advanced_boe_journal_id,
            protests_financial_expenses_boe_account_id = protests_financial_expenses_boe_account_id,
        )
        return res

    # @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.customer_boe_journal_id",
            self.customer_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.supplier_boe_journal_id",
            self.supplier_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.retention_boe_account_id",
            self.retention_boe_account_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.protests_boe_journal_id",
            self.protests_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.protests_financial_expenses_boe_journal_id",
            self.protests_financial_expenses_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.bank_interests_boe_journal_id",
            self.bank_interests_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.round_boe_journal_id",
            self.round_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.bank_claim_journal_id",
            self.bank_claim_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.advanced_boe_journal_id",
            self.advanced_boe_journal_id.id)
        self.env['ir.config_parameter'].sudo().set_param(
            "jp_account_bills_of_exchange.protests_financial_expenses_boe_account_id",
            self.protests_financial_expenses_boe_account_id.id)