# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class SaleOrderShedulingReport(models.Model):
    _name = 'order.scheduling.report'

    name  = fields.Date(string='Date')
    line_id = fields.One2many(comodel_name='order.scheduling.report.line', 
                                inverse_name='report_id',
                                #compute='_compute_line_id', 
                                string='Detail')
    note_ids = fields.One2many(comodel_name='order.scheduling.report.subcription', 
                                inverse_name='report_id', string='Note')
    
    product_id = fields.One2many(comodel_name='order.report.product', 
                                inverse_name='report_id', 
                                string='Product')

    def unlink(self):
        for item in self:
            for line in item.line_id :
                line.unlink
        return super(SaleOrderShedulingReport, self).unlink()

    def compute_qty(self):
        for item in self.line_id:
            order = self.env['sale.order.line'].search([
                ('day_scheduling','=',item.report_id.name),
                ('category','=',item.category.id),
                ('type_scheduling','=',item.name)
            ])
            item.qty = len(order)

    def set_note(self):
        order = self.env['sale.order.line'].search([
                ('day_scheduling','=',self.name)
            ])
        for l in order:
            if l.subscription_id.note_order:
                s = self.env['order.scheduling.report.subcription'].search([('subscription_id','=',l.subscription_id.id),('report_id','=',self.id)])
                if len(s) == 0:
                    self.env['order.scheduling.report.subcription'].create(
                            {
                                'name':l.subscription_id.partner_id.id,
                                'subscription_id':l.subscription_id.id,
                                'category':l.subscription_id.recurring_invoice_line_ids[0].category_id.id,
                                'note_order': l.subscription_id.note_order,
                                'report_id': self.id, 
                            }
                        )
    def set_product(self):
        order = self.env['sale.order'].search([('day_scheduling','=',self.name)])
        for l in order:   
            if l.product_id.product_tmpl_id.id:
                for p in  l.product_id.product_template_attribute_value_ids:
                    if p.attribute_id.id == 19:  
                        s = self.env['order.report.product'].search([
                                    ('name','=',l.product_id.product_tmpl_id.id),
                                    ('report_id','=',self.id),
                                    ('type_producto','=',p.id)
                                    ])
                        if len(s) == 0:
                            self.env['order.report.product'].create(
                                    {
                                        'name':l.product_id.product_tmpl_id.id,
                                        'report_id':self.id,
                                        'type_producto':p.id,
                                        'qty':1,
                                    }
                                )
                        else :
                            s.qty +=1
            

    @api.model
    def _compute_line_id(self):
        for item in self:
            line = self.env['order.scheduling.report.line']
            order = self.env['sale.order.line'].search([
                ('day_scheduling','=',item.name)
            ])
            for l in order:
                t = self.env['order.scheduling.report.line'].search([
                    ('category','=',l.category.id),
                    ('name','=',l.type_scheduling)
                ])
                if len(t) == 0 :
                    self.env['order.scheduling.report.line'].create(
                        {
                            'name':l.type_scheduling,
                            'category':l.category.id,
                            'report_id': item.id
                        }
                    )
            temp = self.env['order.scheduling.report.line'].search([
                ('report_id','=',self.id)
                ])
            if len(temp) > 0 :
                line = temp
            item.line_id = line
            

class SaleOrderShedulingReportLine(models.Model):
    _name = 'order.scheduling.report.line'
    _order = "name desc"

    name = fields.Selection([
        ('breakfast', 'Breakfast'),
        ('mirmorning', 'Mirmorning'),
        ('lunch', 'Lunch'),
        ('mid_afternoon', 'Mid afternoon'),
        ('dinner','dinner')
    ], string='Type')
    category = fields.Many2one(comodel_name='product.category',string='Plan')
    qty = fields.Integer(string='Qty')
    report_id = fields.Many2one(comodel_name='order.scheduling.report', string='Report')
    
    @api.model
    def _compute_qty(self):
        for item in self:
            order = self.env['sale.order.line'].search([
                ('day_scheduling','=',item.report_id.name),
                ('category','=',item.category.id),
                ('type_scheduling','=',item.name)
            ])
            item.qty = len(order)

class SaleOrderShedulingReportSubcription(models.Model):
    _name = 'order.scheduling.report.subcription'
    _order = "category desc"

    name = fields.Many2one(comodel_name='res.partner', string='Partner')
    category = fields.Many2one(comodel_name='product.category',string='Plan')
    subscription_id = fields.Many2one(comodel_name='sale.subscription', string='subscription')
    note_order = fields.Char(string='Note')
    report_id = fields.Many2one(comodel_name='order.scheduling.report', string='Report')

class SaleOrderReportProduct(models.Model):
    _name = 'order.report.product'

    name = fields.Many2one(comodel_name='product.template', string='Producto')
    type_producto = fields.Many2one(comodel_name='product.template.attribute.value',string='Tipo')
    report_id = fields.Many2one(comodel_name='order.scheduling.report', string='Report')
    qty = fields.Integer(string='Qty')