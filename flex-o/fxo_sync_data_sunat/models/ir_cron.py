# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
import threading
import time
import psycopg2
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_intervalTypes = {
        'days': lambda interval: relativedelta(days=interval),
        'hours': lambda interval: relativedelta(hours=interval),
        'weeks': lambda interval: relativedelta(days=7 * interval),
        'months': lambda interval: relativedelta(months=interval),
        'minutes': lambda interval: relativedelta(minutes=interval),
        'seconds': lambda interval: relativedelta(seconds=interval),
    }

class ir_cron(models.Model):
    _inherit = "ir.cron"
    interval_type = fields.Selection([('seconds', 'Seconds'),
                                      ('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')

    @classmethod
    def _process_job(cls, job_cr, job, cron_cr):
        """ Run a given job taking care of the repetition.

        :param job_cr: cursor to use to execute the job, safe to commit/rollback
        :param job: job to be run (as a dictionary).
        :param cron_cr: cursor holding lock on the cron job row, to use to update the next exec date,
            must not be committed/rolled back!
        """
        try:
            with api.Environment.manage():
                cron = api.Environment(job_cr, job['user_id'], {})[cls._name]
                # Use the user's timezone to compare and compute datetimes,
                # otherwise unexpected results may appear. For instance, adding
                # 1 month in UTC to July 1st at midnight in GMT+2 gives July 30
                # instead of August 1st!
                now = fields.Datetime.context_timestamp(cron, datetime.now())
                nextcall = fields.Datetime.context_timestamp(cron, fields.Datetime.from_string(job['nextcall']))
                numbercall = job['numbercall']

                ok = False
                while nextcall < now and numbercall:
                    if numbercall > 0:
                        numbercall -= 1
                    if not ok or job['doall']:
                        cron._callback(job['cron_name'], job['ir_actions_server_id'], job['id'])
                    if numbercall:
                        nextcall += _intervalTypes[job['interval_type']](job['interval_number'])
                addsql = ''
                if not numbercall:
                    addsql = ', active=False'
                cron_cr.execute("UPDATE ir_cron SET nextcall=%s, numbercall=%s" + addsql + " WHERE id=%s",
                                (fields.Datetime.to_string(nextcall.astimezone(pytz.UTC)), numbercall, job['id']))
                cron.invalidate_cache()

        finally:
            job_cr.commit()
            cron_cr.commit()

"""
_name = "ir.cron"
    _order = 'cron_name'
    _description = 'Scheduled Actions'

    ir_actions_server_id = fields.Many2one(
        'ir.actions.server', 'Server action',
        delegate=True, ondelete='restrict', required=True)
    cron_name = fields.Char('Name', related='ir_actions_server_id.name', store=True)
    user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)
    active = fields.Boolean(default=True)
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='months')

"""