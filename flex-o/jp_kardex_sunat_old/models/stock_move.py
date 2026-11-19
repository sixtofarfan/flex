# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
import pytz
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    kardex_price_unit = fields.Float(string='Kardex Price Unit', default=0) # digits=(total, decimal)

    def _create_in_svl(self, forced_quantity=None):
        res = super(StockMove, self)._create_in_svl()
        for valuation in res:
            # Si existen ajustes de inventario inicial
            if valuation.stock_move_id.inventory_id:
                for line in valuation.stock_move_id.inventory_id.line_ids:
                    if line.product_id == valuation.product_id and line.location_id == valuation.stock_move_id.location_dest_id and line.sunat_code == '16':
                        valuation.update({
                            'unit_cost': line.initial_cost,
                            # 'unit_cost_foreign': line.initial_cost / line.currency_id._get_conversion_rate(line.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, line.inventory_date or datetime.datetime.now()) if line.currency_id else 1,
                            'value': line.initial_cost * valuation.quantity,
                            'remaining_value': line.initial_cost * valuation.quantity
                            })
                        # print(line.product_id.name)
                        # print(line.location_id.name)
                        # print(line.product_qty)
                        # print(line.initial_cost)
                        line.product_id.last_cost_kardex = line.initial_cost
            else:
                if valuation.stock_move_id.purchase_line_id:
                    price_unit = valuation.stock_move_id.purchase_line_id.price_unit
                else:
                    if valuation.stock_move_id.origin_returned_move_id:
                        vl = self.env['stock.valuation.layer'].search([('stock_move_id','=', valuation.stock_move_id.origin_returned_move_id.id),('product_id','=',valuation.stock_move_id.product_id.id),('quantity','!=',0)])
                        price_unit = vl.unit_cost
                    else:
                        # TODO pensar como hacer para mover productos de una almacen a otro
                        # que pueden tener costo valorizados distintos
                        price_unit = valuation.stock_move_id.product_id.last_cost_kardex
                # price_unit_foreign = price_unit
                if valuation.stock_move_id.purchase_line_id.currency_id and valuation.stock_move_id.purchase_line_id.currency_id != self.env.user.company_id.currency_id:
                    rate = valuation.currency_id._get_conversion_rate(valuation.stock_move_id.purchase_line_id.currency_id, self.env.user.company_id.currency_id, self.env.user.company_id, valuation.stock_move_id.picking_id.kardex_date if valuation.stock_move_id.picking_id.use_kardex_date else valuation.stock_move_id.picking_id.scheduled_date)
                    if valuation.stock_move_id.picking_id.invoice_id: # or valuation.stock_move_id.picking_id.invoice_id_purchase:
                        # if valuation.stock_move_id.picking_id.invoice_id:
                        if valuation.stock_move_id.picking_id.invoice_id.tc_per:
                            price_unit = price_unit * valuation.stock_move_id.picking_id.invoice_id.currency_rate
                        else:
                            price_unit = price_unit * rate
                    else:
                        price_unit = price_unit * rate
                valuation.update({
                    'unit_cost': price_unit,
                    # 'unit_cost_foreign': price_unit_foreign,
                    'value': price_unit * valuation.quantity,
                    'remaining_value': price_unit * valuation.quantity  
                })
        return res

    @api.model_create_multi
    def create(self, vals_list):
        #TODO verificar doble movimiento al confirmar pedido tiene un posible error
        # revisar los movimientos de inventario
        res = super(StockMove, self).create(vals_list)
        # Verfica antes de crear algun movimiento si el periodo de kardex esta cerrado
        # Se obtiene el periodo de la fecha del movimiento
        move_date = res[0].date
        # Si el movimiento tiene un picking se obtiene la fecha kardex
        if res[0].picking_id:
            move_date = res[0].picking_id.kardex_date or res[0].picking_id.date
        # Si el movimiento tiene un ajuste de inventarios se obtiene la fecha
        # del inventario o la fecha contable si tuviera
        if res[0].inventory_id:
            if res.inventory_id.accounting_date:
                move_date = res[0].inventory_id.accounting_date
            else:
                move_date = res[0].inventory_id.date
        # TODO si hay produccion hacer lo mismo para obtener la fecha de mrp
        # TODO Falta hacer debug a esta funcion para que la fecha no se pase por 5 horas
        locked_period = str(move_date.year) + '-' + str(move_date.month).zfill(2)
        closed_period = self.env['closing.period'].search([('locked_period', '=', locked_period),'|',('location_ids','in',res[0].location_id.id),('location_ids','in', res[0].location_dest_id.id),('state','=','done')])
        if closed_period:
            raise UserError(_('The move you want to create belongs to a period allready closed in inventory.'))
        return res

    @api.onchange('date_expected','date')
    def onchange_date(self):
        res = super(StockMove, self).onchange_date()
        if self.picking_id:
            self.date = self.picking_id.kardex_date
        return res

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    # Esto sirve para los reportes de inventario como las tablas pivot
    kardex_date = fields.Datetime(string='Kardex Date')#related='picking_id.kardex_date')

    def compute_kardex_date(self):
        move_ids = self.env['stock.move'].search([])
        for move in move_ids:
            k_date = move.date
            if move.inventory_id:
                if move.inventory_id.accounting_date:
                    k_date = self.convert_TZ_to_USER(datetime.strftime(move.inventory_id.accounting_date,"%Y-%m-%d %H:%M:%S"))
                else:
                    k_date = move.inventory_id.date
            if move.picking_id:
                k_date = move.picking_id.kardex_date
            for line in move.move_line_ids:
                line.kardex_date = k_date

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