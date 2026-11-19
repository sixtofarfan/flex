# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PeriodDate(models.Model):
    _name = 'period.date'

    name = fields.Char('Name')
    date_from  = fields.Date(string='From')
    date_to = fields.Date(string='To')
    
    
