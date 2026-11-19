# -*- coding: utf-8 -*-

from odoo import _, fields, models


class Stock_Picking(models.Model):
    _inherit = "stock.picking"

    fxo_analytic_account_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica")


class Stock_Move(models.Model):
    _inherit = "stock.move"

    fxo_analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Cuenta Analitica", related="picking_id.fxo_analytic_account_id"
    )
