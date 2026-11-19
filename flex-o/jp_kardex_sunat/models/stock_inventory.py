# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
import pytz

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    # is_initial = fields.Boolean(string='Is Initial?')
    type_operation_sunat_id = fields.Many2one('type.operation.kardex','Tipo de Operación SUNAT')

    def action_view_related_inventory_lines(self):
        self.ensure_one()
        domain = [('inventory_id', 'in', self.ids)]
        action = {
            'name': _('Inventory Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.inventory.line',
            'view_type': 'list',
            'view_mode': 'list,form',
            'domain': domain,
        }
        return action

    def action_validate(self):
        res = super(StockInventory, self).action_validate()
        if self.accounting_date:
            k_date = self.accounting_date
        else:
            k_date = self.date
        k_date = self.convert_TZ_to_USER(datetime.strftime(k_date, "%Y-%m-%d %H:%M:%S"))
        for move in self.move_ids:
            for line in move.move_line_ids:
                line.kardex_date = k_date
        return res

    def convert_TZ_to_USER(self, TZ_datetime):
        from datetime import datetime
        fmt = "%Y-%m-%d %H:%M:%S"
        # Current time in UTC
        now_utc = datetime.now(pytz.timezone('UTC'))
        # Convert to current user time zone
        now_timezone = now_utc.astimezone(pytz.timezone(self.env.user.tz))
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_timezone.strftime(fmt), fmt) - datetime.strptime(now_utc.strftime(fmt), fmt)
        local_datetime = datetime.strptime(TZ_datetime, fmt)
        result_user_datetime = local_datetime - UTC_OFFSET_TIMEDELTA
        return result_user_datetime

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    initial_cost = fields.Float(string='Initial Cost', digits='Kardex Cost')
    sunat_code = fields.Char(store=True, related='inventory_id.type_operation_sunat_id.code', string='Código de tipo de operación SUNAT')
    currency_id = fields.Many2one('res.currency', string='Purchase currency')

class StockValuationLayer(models.Model):

    _inherit = 'stock.valuation.layer'

    # Adicional de digitos al campo (8)
    unit_cost = fields.Float('Unit Value', readonly=True, digits='Kardex Cost')
    # unit_cost_foreign = fields.Float('Unit Value Foreign', readonly=True, digits='Kardex Cost')