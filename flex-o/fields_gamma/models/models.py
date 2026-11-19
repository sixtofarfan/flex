# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class SaleOrderExtraFields(models.Model):
    _inherit = "sale.order"
    
    type_service = fields.Char(string="Type service")
    internal_ref = fields.Char(string="Internal ref")
    internal_ref_child = fields.Char(string="Internal ref child")
    internal_ref_grandchild = fields.Char(string="Internal ref grandchild")         
    internal_ref_great_grandson = fields.Char(string="Internal ref great grandson")
    shipper_name = fields.Char(string="Shipper name")
    consignne_name = fields.Char(string="Consignne name")
    via = fields.Char(string="Via")
    salesman_name = fields.Char(string="Salesman name")
    tracing_name = fields.Char(string="Tracing name")
    operations_name = fields.Char(string="Operations name")
    flight_number = fields.Char(string="Flight number")
    flight_date = fields.Date(string="Flight date")
    finishing_date = fields.Date(string="Finishing date")
    origin_country = fields.Char(string="Origin country")
    origin_port = fields.Char(string="Origin port")
    destination_country = fields.Char(string="Destination country")
    destination_city = fields.Char(string="Destination city")
    foreign_agent_name = fields.Char(string="Foreign agent name")
    naviera_name = fields.Char(string="Naviera name")
    delivery_master_number = fields.Char(string="Delivery master number")
    delivery_child_number = fields.Char(string="Delivery child number")  
    delivery_grandchild_number = fields.Char(string="Delivery grandchild number")
    delivery_great_grandson_number = fields.Char(string="Delivery great grandson number")
    cda_number = fields.Char(string="CDA number")
    year_dam_number = fields.Char(string="Year dam number")
    regime_name = fields.Char(string="Regime name")
    dispach_type = fields.Char(string="Dispachtype")
    sada_type = fields.Char(string="Sada type")
    name_booking = fields.Char(string="Name booking")
    load_type = fields.Char(string="Load type")
    rights_payments = fields.Char(string="Rights payments")
    amount_untaxed1 = fields.Char(string="Amount untaxed")
    freight_value = fields.Char(string="Freight value")
    safe_value = fields.Char(string="Safe value")
    cif_value = fields.Char(string="CIF value")
    ady_total = fields.Char(string="Ady total")
    amount_tax1 = fields.Char(string="Amount tax")
    ipm_total = fields.Char(string="IPM total")
    perception_total = fields.Char(string="Total perception")
    terminal_name = fields.Char(string="Terminal name")
    numbering_date = fields.Date(string="Numbering date")
    freight_condition = fields.Char(string="Freight condition")
    quotation = fields.Char(string="Quotation")

    cda_number_perception  = fields.Char(string="Numero de Percepción")

    date_invoicing = fields.Date(string="Date Invoicing")
    date_verify  = fields.Datetime(string="Date verify")
    
    date_done = fields.Date(string="Date Done")

    situation_payment = fields.Boolean(string='Situation Payment')

    total_volumen = fields.Float(string='Total Volumen')

    total_wieght  = fields.Float(string='Total Wiegth')
    
    
    
class SaleOrderExtraFields(models.Model):
    _inherit = "sale.order.type"

    code = fields.Char(string='Codigo')
    
class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"
    
    code = fields.Char(string='Codigo')

class AccountMove(models.Model):
    _inherit = "account.move"
    
    type_invoice  = fields.Selection(string='Tipo de factura', selection=[('O', 'Operativa'), ('A', 'Administrativa'),],default='A')
    invoice_expo_user_id = fields.Many2one(comodel_name='res.users', string='Vendedor expo.')
    corporate_reference = fields.Char(string='Ref. Corporativa')
    shipping_documents = fields.Char(string='Booking/BL')
    
    
    

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    order_id = fields.Many2one(comodel_name='sale.order', string='#Operac.')
    type_id = fields.Many2one(related='order_id.type_id',comodel_name='sale.order.type',readonly=True)
    internal_ref = fields.Char(related='order_id.internal_ref', string='Internal Ref', readonly=True)
    internal_ref_child = fields.Char(related='order_id.internal_ref_child',string="Internal ref child",readonly=True)
    type_invoice = fields.Selection(related='move_id.type_invoice', string="Tipo de factura",readonly=True)

    @api.onchange('order_id')
    def get_analytic_account(self):
        for rec in self:
            if not rec.analytic_account_id and rec.order_id.analytic_account_id:
                rec.analytic_account_id = rec.order_id.analytic_account_id.id

class AccountPayment(models.Model):
    _inherit = "account.payment"

    order_id = fields.Many2one(comodel_name='sale.order', string='#Operac.')
    internal_ref = fields.Char(related='order_id.internal_ref',string="Internal ref", readonly=True)
    is_advance = fields.Boolean(string='Es Anticipo')

class ResPartner(models.Model):
    _inherit = "res.partner"

    invoice_expo_user_id = fields.Many2one(comodel_name='res.users', string='Vendedor expo.')
