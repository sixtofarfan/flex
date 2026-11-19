# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from . import get_value
from datetime import date, datetime  # as dt, timedelta as td
# from dateutil.relativedelta import relativedelta
from calendar import monthrange
from odoo.exceptions import UserError


class ClosingPeriod(models.Model):
    _name = 'closing.period'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _description = 'Closing Period'
    _order = 'locked_period desc'

    name = fields.Char(string='Name', tracking=True)
    locked_period = fields.Char(string='Period',
                                default=str(monthrange(date.today().year, date.today().month)[1]) + '-' + str(
                                    date.today().month))
    initial_date = fields.Date(string='Initial Date', default=date.today().replace(day=1), tracking=True)
    end_date = fields.Date(string='End Date',
                           default=date.today().replace(day=monthrange(date.today().year, date.today().month)[1]),
                           tracking=True)
    data_date = fields.Datetime(string='Retrieve Date', tracking=True)
    lock_date = fields.Date(string='Lock Date', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('data', 'Retrieved'),
        ('done', 'Done'),
    ], string='State', default='draft', tracking=True)
    period_lines = fields.One2many('closing.period.line', 'period_id', string='Period Lines', tracking=True,
                                   domain=[('is_negative', '=', False)])
    period_lines_errors = fields.One2many('closing.period.line', 'period_id', string='Period Lines Errors',
                                          tracking=True, domain=[('is_negative', '=', True)])
    company_id = fields.Many2one(comodel_name='res.company', default=(lambda self: self.env.user.company_id),
                                 required=True, string='Company', store=True)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True, related='company_id.currency_id',
                                          store=True)
    location_ids = fields.Many2many('stock.location', string='Location', tracking=True)

    def unlink(self):
        for period in self:
            if period.state == 'done':
                raise UserError(_('You cant delete a period with done state'))
        return super(ClosingPeriod, self).unlink()

    @api.onchange('initial_date')
    def _onchange_initial_date(self):
        self.locked_period = str(self.initial_date.year) + '-' + str(self.initial_date.month).zfill(2)

    @api.constrains('initial_date', 'end_date', 'locked_period')
    def _check_dates(self):
        if self.initial_date > self.end_date:
            raise UserError(_('End date must be greather than initial date.'))
        if self.initial_date.month != self.end_date.month:
            raise UserError(_('End date and initial date must be in the same period.'))

    def _search_location_period(self):
        period_id = self.env['closing.period'].search(
            [('locked_period', '=', self.locked_period), ('location_ids', 'in', self.location_ids.ids),
             ('state', '=', 'done')])
        if period_id:
            raise UserError(_('There is a closing period with the same location and locked period.'))

    def get_cost(self):
        if self.state == 'data':
            self.clear_lines()
            return
        self._check_dates()
        self._search_location_period()
        ck = get_value.ComputeKardex()
        vals = []
        product_ids = self.env['product.product'].search([])
        for location in self.location_ids:
            for product in product_ids:
                kardex_cost = ck.get_kardex_close_period(product.id, self.locked_period, location.id,
                                                         self.end_date.strftime('%Y-%m-%d 23:59:59'), self.env)
                val = {
                    'period_id': self.id,
                    'product_id': product.id,
                    'location_id': location.id,
                    'uom_uom': product.uom_id.id,
                    'quantity': kardex_cost['total_q'],
                    'unit_cost': kardex_cost['unit_cost']
                }
                if val['quantity'] < 0:
                    val.update({'is_negative': True})
                if val['quantity'] != 0:
                    vals.append(val)
        self.period_lines.unlink()
        self.env['closing.period.line'].create(vals)
        self.data_date = datetime.now()
        self.state = 'data'

    def close(self):
        self.lock_date = date.today()
        self.state = 'done'

    def check_previous_period(self):
        close_period = self.env['closing.period'].search(
            [('locked_period', '>', self.locked_period), ('state', '=', 'done')])
        if close_period:
            return True

    def cancel(self):
        if self.check_previous_period():
            raise UserError(
                _('This period cannot be canceled because there is a later period. Cancel all of the above first.'))
        self.clear_lines()

    def clear_lines(self):
        self.data_date = False
        self.lock_date = False
        self.period_lines.unlink()
        self.period_lines_errors.unlink()
        self.state = 'draft'


class ClosingPeriodLine(models.Model):
    _name = 'closing.period.line'
    _description = 'Closing Period Line'
    _order = 'location_id, product_id'

    period_id = fields.Many2one('closing.period', string='Period')
    location_id = fields.Many2one('stock.location', string='Location')
    product_id = fields.Many2one('product.product', string='Product')
    uom_uom = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float('Product quantity', digits='Product Unit of Measure', default=0.0)
    unit_cost = fields.Float(string='Unit cost', digits='Kardex Cost')
    is_negative = fields.Boolean(string='Is negative?')
