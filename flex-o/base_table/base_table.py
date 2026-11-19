# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#     Copyright (C) 2011 Nanotec-cu - Nanotec-cu SAC (<http://nanotec.com.pe>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

#from openerp.osv import osv, fields
#from openerp.tools.translate import _
from odoo import api, fields, models, _
import time
from odoo.exceptions import UserError

#class base_table(osv.osv):
class base_table(models.Model):

    def name_get(self):
        ids = self._ids
        if not len(ids):
            return []
        reads = self.read(['name','code','description'])
        res = []
        for record in reads:
            name = "%s%s%s"%(record['name'], record['description'] and ' - ' or '', record['description'] or '') 
            if record['code']:
                name = '[%s] %s'%(record['code'],name)
            res.append((record['id'], name))
        return res

    def _name_get_fnc(self):
        for rec in self:
            res = rec.name_get()
            for item in res:
               rec.complete_name = item[1]

    _name = 'base.table'
    _description = 'Base Table of Tables'

    company_id = fields.Many2one('res.company',string='Company')
    country_id = fields.Many2one('res.country',string='Company')
    code = fields.Char(string='Code', size=32, required=True)
    name = fields.Char(string='Name', size=2048, required=True, translate=True)
    complete_name = fields.Char(compute="_name_get_fnc", string="Name")
    description = fields.Text(string='Table Description')
    parent_id = fields.Many2one('base.table',string='Parent Table', domain=[('type','=','view')])
    child_ids = fields.One2many('base.table', 'parent_id', string='Child Tables')
    type = fields.Selection(selection=[('view','View'), ('normal','Normal')], string='Table Type', default='normal')
    active = fields. Boolean(string='Active', default=True)
    element_ids = fields.One2many('base.element','table_id',string="Elements")

    _sql_constraints = [('code_unique','unique(company_id,code)',_('The code must be unique!'))]
    _order = "code"
    
    def _check_recursion(self):
        ids = list(self._ids)
        level = 100
        while len(ids):
            self._cr.execute('select distinct parent_id from base_table where id IN %s',(tuple(ids),))
            ids = filter(None, map(lambda x:x[0], self._cr.fetchall()))
            if not level:
                return UserError(_('Error ! You can not create recursive table of tables.'))
            level -= 1
        return True

    def child_get(self, cr, uid, ids):
        return [ids]
    
#class base_element(osv.osv):
class base_element(models.Model):
    _name = 'base.element'
    _description = 'Elements in table of tables'

    table_id = fields.Many2one('base.table',string='Base Table')
    code = fields.Char(string='Element Code', size=32)
    name = fields.Char(string='Element Name', size=64, required=True)
    description = fields.Text(string='Element Description')
    element_char = fields.Char(string='Element String', size=1024)
    element_float = fields.Float(string='Element Float')
    element_percent = fields.Float(string='Element Percent', help="Insert the number without the percent symbol. Examples = for 100% is 100, for 3.75% is 3.75")
    element_date = fields.Date(string='Element Date')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    interval_init_infinity = fields.Boolean(string='Infinity Negative', default=True)
    interval_init_close = fields.Boolean(string='Value >= Interval Initial')
    interval_init = fields.Float(string='Inverval Initial')
    interval_end_infinity = fields.Boolean(string='Infinity Positive', default=True)
    interval_end_close = fields.Boolean(string='Value <= Interval End')
    interval_end = fields.Float(string='Inverval End')
    sequence = fields.Integer(string='Sequence', default=5)
    active = fields.Boolean(string='Active', default=True)


    _sql_constraints = [('table_name_unique','unique(table_id,name,start_date,interval_init)',_('The element code must be unique for this table!'))]

    def get_element(self, table_code, element_code, field, date=None, interval_value=None, company_id=False):
        sql = "select e.%s from base_element e,base_table t where e.table_id=t.id and t.active=True and e.active=True and t.type<>'view' and t.code='%s' and e.name='%s'"%(field,table_code,element_code)
        sql += self.get_where(date=date,interval_value=interval_value)
        self._cr.execute(sql)
        return self._cr.fetchone()

    def get_elements(self, table_code, field, date=None, interval_value=None, company_id=False):
        sql = "select e.%s from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(field,table_code)
        sql += self.get_where(date=date,interval_value=interval_value)
        self._cr.execute(sql)
        return [x[0] for x in self._cr.fetchall()]

    def get_as_selection(self, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        sql = "select e.name, e.element_char from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(table_code)
        sql += self.get_where(date=date,interval_value=interval_value)
        self._cr.execute(sql)
        return [(x[0],x[1]) for x in self._cr.fetchall()]

    def get_selection(self, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        sql = "select e.name, e.description from base_element e,base_table t where e.table_id=t.id and t.type<>'view' and t.active=True and e.active=True and t.code='%s'"%(table_code)
        sql += self.get_where(date=date,interval_value=interval_value) 
        self._cr.execute(sql)
        return [(x[0],x[1]) for x in self._cr.fetchall()]

    def get_where(self,date=None, interval_value=None, company_id=False):
        res = ''
        if date: res += " and coalesce(start_date,'%s')<='%s' and coalesce(end_date,'%s')>='%s'"%(date,date,date,date)
        if interval_value is not None:
            res += " and case when interval_init_infinity then %s else interval_init + (case when interval_init_close then 0 else 0.00000000000001 end) end  <= %s"%(interval_value,interval_value)
            res += " and case when interval_end_infinity then %s else interval_end - (case when interval_end_close then 0 else 0.00000000000001 end) end >= %s"%(interval_value,interval_value)
        if company_id:
            res += " and (company_id is null or company_id=%s)"%company_id
        return res

    def browse_elements(self, table_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        return self.browse(self.get_elements(table_code,'id',date=date,interval_value=interval_value,company_id=company_id))

    def element_exists(self, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        return bool(self.get_element(table_code,element_code,'id',date=date,interval_value=interval_value,company_id=company_id))

    def get_element_percent(self, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_code,'element_percent',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0] or 0.0

    def get_percent(self, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_name,'element_percent',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0]/100.0 or 0.0

    def get_element_float(self, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_code,'element_float',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0] or 0.0

    def get_float(self, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_name,'element_float',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0] or 0.0

    def get_element_char(self, table_code, element_code, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_code,'element_char',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0] or ''

    def get_char(self, table_code, element_name, date=time.strftime('%Y-%m-%d'), interval_value=None, company_id=False):
        val = self.get_element(table_code,element_name,'element_char',date=date,interval_value=interval_value,company_id=company_id)
        return val and val[0] or ''


