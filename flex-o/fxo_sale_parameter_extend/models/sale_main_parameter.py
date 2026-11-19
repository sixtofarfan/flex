# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class fxoSaleMainParameter(models.Model):
    _name = 'fxo.sale.main.parameter'

    name = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id)

    expiration_type = fields.Selection(string='Vencer a los (Dias/Mes/Años) ', selection=[
        ('Days', 'Days'),
        ('months', 'Months'),
        ('year', 'Year')], default="Days")
    expiration = fields.Integer(string='Cantidad')
    gross_profit_percent = fields.Float(string='Porcentaje margen de utilidad')
    commission_percent_expenses = fields.Float(string='% Comisión sobre el costo')
    cant_commission = fields.Integer(string='Mes de Comisión')

    producto_renta_mensual = fields.Many2one(comodel_name='product.product', string='Producto Renta Mensual')

    producto_comision = fields.Many2one(comodel_name='product.product', string='Producto Comision')
    producto_costo_instalacion = fields.Many2one(comodel_name='product.product', string='Producto Costo Instalacion')

    ingresos_id = fields.One2many(comodel_name='fxo.sale.main.parameter.ingreso', inverse_name='parameter_id',
                                  string='Ingreso')
    egreso_id = fields.One2many(comodel_name='fxo.sale.main.parameter.egreso', inverse_name='parameter_id',
                                string='Egreso')


class fxoSaleMainParameter(models.Model):
    _name = 'fxo.sale.main.parameter.ingreso'

    name = fields.Many2one(comodel_name='product.template', string='Producto')
    parameter_id = fields.Many2one(comodel_name='fxo.sale.main.parameter', string='Parameter')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id)


class fxoSaleMainParameter(models.Model):
    _name = 'fxo.sale.main.parameter.egreso'

    name = fields.Many2one(comodel_name='product.template', string='Producto')
    parameter_id = fields.Many2one(
        comodel_name='fxo.sale.main.parameter', string='Parameter')
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company.id)
