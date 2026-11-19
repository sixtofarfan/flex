# -*- coding: utf-8 -*-

import logging

from ast import literal_eval
from collections import defaultdict
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.misc import ustr
import datetime

class Cron_class_temp(models.Model):
    _name = 'cron.class.temp'

    @api.model
    def update_seller(self):
        for i in self.env['sale.order'].search([('state','in',('done','sale'))]):
            if len(i.team_id.destination_sales_team)>0 and i.team_id.expiration_days>0:
                fechaX = i.date_order
                boolr= False
                perm = self.env['crm.team.router.request'].search([('state','=','done'),('partner_id','=',i.partner_id.id),('user_id','=',i.partner_id.user_id.id)])
                if len(perm)>0:
                    fechaX = per[0].date_due
                    boolr = (datetime.datetime.now()- fechaX).days >=0
                else:
                    boolr = (datetime.datetime.now()- fechaX).days >= i.team_id.expiration_days

                if boolr:
                    self.env.cr.execute(""" Update sale_order set team_id = """ + str(i.team_id.destination_sales_team[0].id) + " where id = " + str(i.id) + " ;" )
                    
                    if len(i.team_id.destination_sales_team[0].member_ids)>0:
                        i.partner_id.user_id = False
                        menor = i.team_id.destination_sales_team[0].member_ids[0]
                        cont = len( self.env['res.partner'].search([('user_id','=',menor.id)]) )
                        for us in i.team_id.destination_sales_team[0].member_ids:
                            if len( self.env['res.partner'].search([('user_id','=',us.id)]) )< cont:
                                cont = len( self.env['res.partner'].search([('user_id','=',us.id)]) )
                                menor = us

                        self.env.cr.execute(""" Update sale_order set user_id = """ + str(menor.id) + " where id = " + str(i.id) + " ;" )        
                        i.partner_id.user_id = menor.id
        return True