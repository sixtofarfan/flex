# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_nubyx = fields.Boolean(string="Es Nubyx", default=False)
    product_rel_id = fields.Many2one("product.product", "Producto")
    bool_is_factibility = fields.Boolean(string="Necesita Factibilidad", default=False)
    bool_qty_street = fields.Boolean(string="Necesita Direccion", default=False)
    bool_is_study_economic = fields.Boolean(string="Necesita Estudio Economico", default=False)
    edit_price_unit = fields.Selection(
        string="Edit Price Unit ",
        selection=[
            ("none", "None"),
            ("edit", "Edit"),
        ],
        default="edit",
    )

    fxo_cost_price = fields.Float("Precio de Costo")
    fxo_cost_price_currency = fields.Many2one("res.currency", "Moneda de Costo")
    porcent_aprove = fields.Float("Porcentaje por Defecto Estudio Economico", default="35")
    transport_physic = fields.Selection(
        [("Fibra Optica", "Fibra Optica"), ("Radioenlace", "Radioenlace"), ("Satelital", "Satelital")],
        "Medio Transporte Fisico",
    )

    @api.onchange("bool_is_factibility")
    def onchange_is_factibility(self):
        for i in self:
            if i.bool_is_factibility:
                i.bool_is_study_economic = True

    @api.onchange("bool_is_study_economic")
    def onchange_is_factibility(self):
        for i in self:
            if i.bool_is_factibility and i.bool_is_study_economic == False:
                i.bool_is_study_economic = True
