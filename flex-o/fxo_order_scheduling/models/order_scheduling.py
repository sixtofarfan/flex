# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError

class SaleOrderSheduling(models.Model):
    _name = 'sale.order.scheduling'

    name = fields.Char()
    period_id = fields.Many2one(comodel_name='period.date', string='Period')
    category_id = fields.Many2one(comodel_name='product.category',
                                  string='Category')
    line_id = fields.One2many(comodel_name='sale.order.scheduling.line',
                              inverse_name='scheduling_id',
                              string='Products')

    state = fields.Selection([  ('draft', 'Draft'),
                                ('process','Process') ,
                                ('done', 'Done')],
                             string='State',
                             default='draft')

    order_ids = fields.One2many(comodel_name='sale.order.scheduling.order',
                                inverse_name='scheduling_id',
                                #compute='_compute_order_line',
                                string='Order')

    order_id = fields.Many2many(comodel_name='sale.order', string='Order')
    order_count = fields.Integer(compute='_compute_order_count' ,string='Order Count')

    @api.model
    def _compute_order_line(self):
        for item in self:
            item.order_ids = self.env['sale.order.scheduling.order']
            for line in item.line_id :
                count = self.env['sale.order.scheduling.order'].search([
                    ('name','=',line.name),
                    ('scheduling_id','=',line.scheduling_id.id)
                ])
                if len(count) == 0 :
                    temp = self.env['sale.order.scheduling.order'].create({
                        'name':line.name,
                        'scheduling_id':line.scheduling_id.id
                    })
                    item.order_ids += temp
                else :
                    item.order_ids += count


    def action_view_order(self):
        orders = self.mapped('order_id')
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('id', 'in', orders.ids)]
        return action

    @api.model
    def _compute_order_count(self):
        for item in self:
            item.order_count = len(item.order_id)

    def generate_sale_order(self):
        subscription_line = self.env['sale.subscription.line'].search([
            ('category_id', '=', self.category_id.id),
            # ('date_start', '>=', str(self.period_id.date_from)),
            #('recurring_next_date', '<=', str(self.period_id.date_to)),
        ])

        for line in subscription_line:
            self.create_order(line)
        self.state = 'process'

    def set_draft(self):
        for item in self.order_id:
            item.unlink()
        for item in self.order_ids:
            item.unlink()
        self.state = 'draft'

    def confirm(self):
        self.state = 'process'

    def set_done(self):
        self.state = 'done'

    # def create_order(self,subscription_line):

    #     date_to = subscription_line.recurring_next_date
    #     date_from = subscription_line.date_start
    #     hr_holidays_public = self.env['hr.holidays.public'].search([
    #         ('year', '=', date_from.year)
    #     ])

    #     anality_id = 0
    #     if subscription_line.analytic_account_id.analytic_account_id.id:
    #         anality_id = subscription_line.analytic_account_id.analytic_account_id.id

    #     line_ids = self.line_id
    #     if len(line_ids) > 0 :
    #         # days = subscription_line.product_id.uom_id.factor_inv
    #         days = subscription_line.product_id.days

    #         for item in line_ids:
    #             date_day = datetime.strptime(str(item.name) + " 08:00:00",'%Y-%m-%d %H:%M:%S')
    #             dayofweek = datetime.weekday(item.name)

    #             order_subscription = self.env['sale.order.line'].search([
    #                ('commitment_date','=',date_day),
    #                ('subscription_id','=', subscription_line.id)
    #             ])
    #             hr_holidays_public_line = self.env['hr.holidays.public.line'].search([
    #                 ('year_id', '=', hr_holidays_public.id),
    #                 ('date','=',item.name)
    #             ])
    #             if len(order_subscription) == 0 and len(hr_holidays_public_line) == 0 :
    #                 if item.name >= date_from and item.name <= date_to and dayofweek < days:
    #                     data =  {
    #                                 'partner_id': subscription_line.analytic_account_id.partner_id.id,
    #                                 'commitment_date': date_day,
    #                                 'date_order' : date_day,
    #                                 'day_scheduling' : date_day,
    #                                 'analytic_account_id': anality_id if anality_id != 0 else False,
    #                                 'product_id': subscription_line.product_id.id ,
    #                                 'category': subscription_line.category_id.id
    #                             }
    #                     order_id = self.env['sale.order'].create(data)
    #                     order_id.date_order = date_day

    #                     address_id = self.env['sale.subscription.address'].search([
    #                         ('day','=',str(dayofweek)),
    #                         ('subscription_id','=',subscription_line.analytic_account_id.id)
    #                     ])
    #                     if len(address_id) > 0:
    #                         order_id.partner_shipping_id = address_id.address_id
    #                     self.order_id += order_id

    #                     for line in item.scheduling_group_id:
    #                         replance = self.env["sale.subscription.order.scheduling"].search([
    #                             ('subscription_id','=',subscription_line.analytic_account_id.id),
    #                             ('product_id','=',line.product_id.id)
    #                             ])
    #                         if len(replance) == 0 :
    #                             data_line = {
    #                                 'order_id': order_id.id,
    #                                 'product_id': line.product_id.id,
    #                                 'subscription_id': subscription_line.analytic_account_id.id
    #                             }
    #                         else :
    #                             data_line = {
    #                                 'order_id': order_id.id,
    #                                 'product_id': replance.product_replance_id.id,
    #                                 'subscription_id': subscription_line.analytic_account_id.id
    #                             }
    #                         self.env['sale.order.line'].create(data_line)

    #                     additional_id = self.env['sale.subscription.order.additional'].search([
    #                         ('day','=',str(dayofweek)),
    #                         ('subscription_id','=',subscription_line.analytic_account_id.id)
    #                     ])
    #                     for line in additional_id:
    #                         data_line = {
    #                                 'order_id': order_id.id,
    #                                 'product_id': line.name.id,
    #                                 'subscription_id': subscription_line.analytic_account_id.id
    #                             }
    #                         self.env['sale.order.line'].create(data_line)

class SaleOrderShedulingLine(models.Model):
    _name = 'sale.order.scheduling.line'

    name = fields.Date(string='Date')
    scheduling_id = fields.Many2one(comodel_name='sale.order.scheduling',string='Period')
    scheduling_group_id = fields.One2many(
        comodel_name='sale.order.scheduling.group',
        inverse_name='name',
        string='Scheduling Day')

    proteins = fields.Float(compute='_compute_proteins', string='Proteins')
    carohydrates = fields.Float(compute='_compute_proteins', string='Carohydrates')
    fats = fields.Float(compute='_compute_proteins', string='Fats')
    calories = fields.Float(compute='_compute_proteins', string='Calories')

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            if self.scheduling_id.period_id.id :
                if self.scheduling_id.period_id.date_from > self.name:
                    raise UserError(_("La fecha  no puede ser menor que el inicio del periodo"))
                if self.scheduling_id.period_id.date_to < self.name:
                    raise UserError(_("La fecha  no puede ser mayor que el Final del periodo"))


    @api.model
    def _compute_proteins(self):
        for item in self:
            for line in item.scheduling_group_id:
                item.proteins += line.proteins
                item.carohydrates += line.carohydrates
                item.fats += line.fats
                item.calories += line.calories

    def generate_sale_order(self):
        subscription_line = self.env['sale.subscription.line'].search([
            ('category_id', '=', self.scheduling_id.category_id.id),
        ])

        for line in subscription_line:
            self.create_order(line)


    def create_order(self,subscription_line):

        #date_to = subscription_line.analytic_account_id.date subscription_line.recurring_next_date
        if subscription_line.analytic_account_id.date:
            date_to = subscription_line.analytic_account_id.date
        else :
            date_to = subscription_line.recurring_next_date
        date_from = subscription_line.analytic_account_id.date_start
        hr_holidays_public = self.env['hr.holidays.public'].search([
            ('year', '=', date_from.year)
        ])

        anality_id = 0
        if subscription_line.analytic_account_id.analytic_account_id.id:
            anality_id = subscription_line.analytic_account_id.analytic_account_id.id


        days = subscription_line.product_id.days

        date_day = datetime.strptime(str(self.name) + " 08:00:00",'%Y-%m-%d %H:%M:%S')
        dayofweek = datetime.weekday(self.name)

        order_subscription = self.env['sale.order.line'].search([
            ('commitment_date','=',date_day),
            ('subscription_id','=', subscription_line.id)
        ])
        hr_holidays_public_line = self.env['hr.holidays.public.line'].search([
            ('year_id', '=', hr_holidays_public.id),
            ('date','=',self.name)
        ])
        if len(order_subscription) == 0 and len(hr_holidays_public_line) == 0 :
            if self.name >= date_from and self.name <= date_to and dayofweek < days:
                data =  {
                            'partner_id': subscription_line.analytic_account_id.partner_id.id,
                            'commitment_date': date_day,
                            'date_order' : date_day,
                            'day_scheduling' : date_day,
                            'analytic_account_id': anality_id if anality_id != 0 else False,
                            'product_id': subscription_line.product_id.id ,
                            'category': subscription_line.category_id.id
                        }
                order_id = self.env['sale.order'].create(data)
                order_id.date_order = date_day

                address_id = self.env['sale.subscription.address'].search([
                    ('day','=',str(dayofweek)),
                    ('subscription_id','=',subscription_line.analytic_account_id.id)
                ])
                if len(address_id) > 0:
                    order_id.partner_shipping_id = address_id.address_id
                self.scheduling_id.order_id += order_id

                for line in self.scheduling_group_id:
                    replance = self.env["sale.subscription.order.scheduling"].search([
                        ('subscription_id','=',subscription_line.analytic_account_id.id),
                        ('product_id','=',line.product_id.id)
                        ])
                    if len(replance) == 0 :
                        data_line = {
                            'order_id': order_id.id,
                            'product_id': line.product_id.id,
                            'type_scheduling': line.type_scheduling,
                            'subscription_id': subscription_line.analytic_account_id.id
                        }
                    else :
                        data_line = {
                            'order_id': order_id.id,
                            'product_id': replance.product_replance_id.id,
                            'type_scheduling': line.type_scheduling,
                            'subscription_id': subscription_line.analytic_account_id.id
                        }
                    self.env['sale.order.line'].create(data_line)

                additional_id = self.env['sale.subscription.order.additional'].search([
                    ('day','=',str(dayofweek)),
                    ('subscription_id','=',subscription_line.analytic_account_id.id)
                ])
                for line in additional_id:
                    data_line = {
                            'order_id': order_id.id,
                            'product_id': line.name.id,
                            'subscription_id': subscription_line.analytic_account_id.id
                        }
                    self.env['sale.order.line'].create(data_line)
        can = self.env['sale.order.scheduling.order'].search([
            ('name', '=', self.name),
            ('scheduling_id', '=', self.scheduling_id.id)
        ])
        if len(can) == 0 :
            self.env['sale.order.scheduling.order'].create(
                {
                    'name':self.name,
                    'scheduling_id':self.scheduling_id.id
                }
            )

class SaleOrderShedulingOrder(models.Model):
    _name = 'sale.order.scheduling.order'
    _order = 'name desc'

    name          = fields.Date(string='Date')
    order_id = fields.Many2many(comodel_name='sale.order',
                                compute='_compute_order',
                                string='Order')
    scheduling_id = fields.Many2one(comodel_name='sale.order.scheduling',string='Scheduling')

    state = fields.Selection([ ('draft', 'Draft'),
                                ('done', 'Done')],
                             string='State',
                             default='draft')
    @api.model
    def _compute_order(self):
        for item in self:
            item.order_id = self.env['sale.order']
            temp = ''
            for line in item.scheduling_id.order_id:
                temp = str(line.commitment_date)
                temp = temp[0:10]
                if str(item.name) == temp:
                    item.order_id += line

    def confirm(self):
        for item in self.order_id:
            if item.state == "draft" :
                item.action_confirm()
        self.state = "done"

    def set_draft(self):
        for item in self.order_id:
            if item.state == "done" :
                item.action_unlock()
                item.action_cancel()
                item.action_draft()
        self.state = "draft"

class SaleOrderShedulingGroup(models.Model):
    _name = 'sale.order.scheduling.group'

    name = fields.Many2one(comodel_name='sale.order.scheduling.line',
                           string='Name')
    type_scheduling = fields.Selection([
        ('breakfast', 'Breakfast'),
        ('mirmorning', 'Mirmorning'),
        ('lunch', 'Lunch'),
        ('mid_afternoon', 'Mid afternoon'),
        ('dinner','dinner')
    ], string='Type')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    proteins = fields.Float(related='product_id.proteins')
    carohydrates = fields.Float(related='product_id.carohydrates')
    fats = fields.Float(related='product_id.fats')
    calories = fields.Float(related='product_id.calories')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    category = fields.Many2one(comodel_name='product.category',
                                  string='Category')
    day_scheduling = fields.Date(string='Scheduling Day')


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    commitment_date = fields.Datetime(related='order_id.commitment_date')
    day_scheduling = fields.Date(related='order_id.day_scheduling')
    category = fields.Many2one(comodel_name='product.category',
                                related='order_id.category',
                                string='Category')

    type_scheduling = fields.Selection([
        ('breakfast', 'Breakfast'),
        ('mirmorning', 'Mirmorning'),
        ('lunch', 'Lunch'),
        ('mid_afternoon', 'Mid afternoon'),
        ('dinner','dinner')
    ], string='Type')
