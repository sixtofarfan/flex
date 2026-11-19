# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FeasibilityCashflowParams(models.Model):
    _name = "fxo_feasibility.params"
    _description = "Cash Flow Feasibility Parameters"
    company_id = fields.Many2one(comodel_name='res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id, readonly=True)

    name = fields.Char()
    gross_profit_percent = fields.Float(string="Profit margin percentage")
    is_default = fields.Boolean(string="Is Default")

    state = fields.Selection(
        string="Status",
        selection=[("draft", "Draft"), ("posted", "Posted")],
        default="draft",
        copy=False,
        readonly=False,
    )

    incomes = fields.One2many(
        comodel_name="fxo_feasibility.params.lines",
        inverse_name="param_incomes_id",
        string="Incomes",
        ondelete="cascade",
    )
    expenses = fields.One2many(
        comodel_name="fxo_feasibility.params.lines",
        inverse_name="param_expenses_id",
        string="Expenses",
        ondelete="cascade",
    )

    def action_draft(self):
        self.write({"state": "draft"})

    def action_post(self):
        self.write({"state": "posted"})

    def unlink(self):
        for record in self:
            if record.state != "draft":
                raise UserError(_("You cannot delete an entry which has been posted once."))
        return super(FeasibilityCashflowParams, self).unlink()


class FeasibilityCashflowParamsIncomes(models.Model):
    _name = "fxo_feasibility.params.lines"
    _description = "Cash Flow Feasibility Parameters Lines"

    param_incomes_id = fields.Many2one(
        "fxo_feasibility.params", string="Param Id Incomes", required=False, ondelete="cascade"
    )
    param_expenses_id = fields.Many2one(
        "fxo_feasibility.params", string="Param Id Expenses", required=False, ondelete="cascade"
    )

    product_id = fields.Many2one("product.product", string="Product", required=True)

    name = fields.Text(string="Description", required=True)
    quantity = fields.Float(string="Quantity", default=1.0)
    additional_profit = fields.Boolean(string="Additional Profit", default=False)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', index=True,
                                 default=lambda self: self.env.company.id)

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.name = self.product_id.get_product_multiline_description_sale()
