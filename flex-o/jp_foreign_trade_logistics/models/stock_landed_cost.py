# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from odoo.tools import float_round

class LandedCost(models.Model):
    _inherit = 'stock.landed.cost'
    
    company_id = fields.Many2one(comodel_name='res.company',default=(lambda self: self.env.user.company_id),required=True,string='Company')
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', readonly=True, related='company_id.currency_id')
    foreign_currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True, string='Foreign Currency')
    amount_total_vendor = fields.Monetary(string='Total vendor bills', currency_field='foreign_currency_id')
    amount_total_vendor_signed = fields.Monetary(string='Total vendor bills', currency_field='company_currency_id')
    amount_total_expenses = fields.Monetary(string='Total expenses', currency_field='foreign_currency_id')
    amount_total_expenses_signed = fields.Monetary(string='Total expenses', currency_field='company_currency_id')
    amount_total_landed = fields.Monetary(string='Total landed cost', currency_field='foreign_currency_id')
    amount_total_landed_signed = fields.Monetary(string='Total landed cost', currency_field='company_currency_id')
    total_quantity = fields.Float(string='Total quantity', digits=(12, 2))
    unit_cost = fields.Float(string='Unit Cost', digits='Cost Determination')
    unit_cost_signed = fields.Float(string='Unit Cost', digits='Cost Determination')
    vendor_bill_ids = fields.One2many('account.move', 'vendor_landed_cost_id', string='Vendor bills')
    expenses_bill_ids = fields.One2many('account.move', 'expenses_landed_cost_id', string='Expenses bills')
    expenses_entry_ids = fields.One2many('account.move.line', 'entry_landed_cost_id', string='Expenses entries')
    product_id = fields.Many2one('product.product', string='Product')
    many_products = fields.Boolean(string='Many products', default = False)
    data_for_report_ids = fields.One2many('data.for.report', 'landed_id', string='Expenses bills')
    import_number = fields.Char(string='Import N°', copy=False)

    def get_valuation_lines(self):
        lines = []
        for move in self.mapped('picking_ids').mapped('move_lines'):
            # it doesn't make sense to make a landed cost for a product that isn't set as being valuated in real time at real cost
            # if move.product_id.valuation != 'real_time' or move.product_id.cost_method not in ('fifo', 'average') or move.state == 'cancel':
            #     continue
            # if sum(move.stock_valuation_layer_ids.mapped('value')) == 0:
            #     precio = sum(move.picking_id.invoice_id.invoice_line_ids.filtered(lambda x: x.product_id == move.product_id).mapped('price_unit'))  * move.picking_id.invoice_id.currency_rate if not move.picking_id.invoice_id.transit_move_line_id else move.picking_id.invoice_id.transit_move_line_id.tc
            #     uom_id = move.picking_id.invoice_id.invoice_line_ids.filtered(lambda x: x.product_id == move.product_id).product_uom_id
            #     # Convertimos toneladas en kilos para hacer lo mismo con e precio
            #     if uom_id != move.product_uom:
            #         if uom_id.uom_type != 'reference':
            #             precio = precio * uom_id.factor
            #     total = precio * move.product_qty
            # else:
            #     total = sum(move.stock_valuation_layer_ids.mapped('value'))
            vals = {
                'product_id': move.product_id.id,
                'move_id': move.id,
                'quantity': move.product_qty,
                'former_cost': sum(move.stock_valuation_layer_ids.mapped('value')),
                'weight': move.product_id.weight * move.product_qty,
                'volume': move.product_id.volume * move.product_qty
            }
            lines.append(vals)

        # if not lines and self.mapped('picking_ids'):
        #     raise UserError(_("You cannot apply landed costs on the chosen transfer(s). Landed costs can only be applied for products with automated inventory valuation and FIFO or average costing method."))
        return lines

    def reset_draft(self):
        svl = self.env['stock.valuation.layer'].search([('stock_landed_cost_id','=',self.id)])
        svl.with_context(force_delete=True).unlink()
        stock_moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
        for move in stock_moves:
            # Cambiamos el costo de producto para la valorización
            svl_qty = self.env['stock.valuation.layer'].search([('product_id', '=', move.product_id.id),('stock_move_id.date','<=',move.date)])
            # move.product_id.last_cost_kardex = move.product_id.last_cost_kardex - float_round(self.amount_total,2) / sum(svl_qty.mapped('quantity'))
            move.product_id.last_cost_kardex = sum(svl_qty.mapped('value')) / sum(svl_qty.mapped('quantity'))
            self._update_moves_price(move, True)
            move.kardex_price_unit = 0 #-= self.amount_total / sum(stock_moves.mapped('product_uom_qty'))
            
        self.state = 'draft'

    def button_validate(self):
        res = super(LandedCost, self).button_validate()  
        self.account_move_id.button_draft()
        self.account_move_id.line_ids.unlink()
        self.account_move_id.name = '/'
        self.account_move_id.unlink()
        self.stock_valuation_layer_ids.with_context(force_delete=True).unlink()
        stock_moves = self.env['stock.move'].search([('picking_id','in',self.picking_ids.ids)])
        landed_unit_cost_signed = float_round(self.amount_total_landed_signed / self.total_quantity,8)
        for move in stock_moves:
            # # Cambiamos el costo de producto para la valorización
            svl_qty = self.env['stock.valuation.layer'].search([('product_id', '=', move.product_id.id),('stock_move_id.date','<=',move.date)])
            move.product_id.last_cost_kardex = sum(svl_qty.mapped('value')) / sum(svl_qty.mapped('quantity'))
            self._update_moves_price(move)
            svl = self.env['stock.valuation.layer'].search([('stock_move_id','=',move.id)])
            if self.many_products:
                total_landed_cost = 0
                first_qty = svl.quantity
                for line in self.valuation_adjustment_lines:
                    if line.product_id == move.product_id and line.quantity == first_qty:
                        total_landed_cost += line.additional_landed_cost
                move.kardex_price_unit = total_landed_cost / first_qty
            else:
                move.kardex_price_unit = landed_unit_cost_signed - svl.unit_cost
        return res
    
    def _update_moves_price(self, move, reset = False):
        if reset:
            svl_qty = self.env['stock.valuation.layer'].search([('product_id', '=', move.product_id.id),('stock_move_id.date','<=',move.date)])
            last_cost_kardex = sum(svl_qty.mapped('value')) / sum(svl_qty.mapped('quantity'))
        else:
            last_cost_kardex = move.product_id.last_cost_kardex
        svl_price = self.env['stock.valuation.layer'].search([('product_id', '=', move.product_id.id),('stock_move_id.date','>=',move.date),('stock_move_id','!=',False),('stock_move_id','!=',move.id)])
        for svl in svl_price:
            if svl.quantity < 0:
                svl.remaining_value = last_cost_kardex * svl.remaining_qty
                svl.value = last_cost_kardex * svl.quantity
                svl.unit_cost = last_cost_kardex 
            else:
                break

    def populate_expenses_bill_ids(self):
        if self.expenses_bill_ids or self.expenses_entry_ids:
            vals = []
            for bill in self.expenses_bill_ids:
                for item in bill.invoice_line_ids:
                    if item.product_id:
                        if bill.currency_id != self.company_currency_id:                                                                        
                            # price_unit = item.price_subtotal * bill.currency_rate
                            foreign_pu = item.price_subtotal
                        else:
                            # price_unit = item.price_subtotal
                            # print(bill.currency_id._get_conversion_rate(self.foreign_currency_id, self.company_currency_id, self.env.user.company_id, bill.invoice_date or  datetime.datetime.now()))
                            foreign_pu = item.price_subtotal / bill.currency_id._get_conversion_rate(self.foreign_currency_id, self.company_currency_id, self.env.user.company_id, bill.invoice_date or  datetime.datetime.now())
                        val = {
                            'cost_id': self.id,
                            'product_id': item.product_id.id if item.product_id else False,
                            'name': item.name,
                            'account_id': item.account_id.id,
                            'price_unit': item.balance, #price_unit * (-1 if bill.type_document_id.code == '07' else 1),
                            'foreign_pu': foreign_pu,
                            'split_method': 'by_quantity',
                            'expense_bill_id': bill.id
                        }
                        vals.append(val)
                    else:
                        raise UserError(_('There is no product selected in the expenses bill %s') %(bill.name))
            for bill in self.vendor_bill_ids:
                for item in bill.invoice_line_ids:
                    if item.product_id and item.product_id.type == 'service':
                        if bill.currency_id != self.company_currency_id:                                                                        
                            # price_unit = item.price_subtotal * bill.currency_rate
                            foreign_pu = item.price_subtotal
                        else:
                            # price_unit = item.price_subtotal
                            foreign_pu = item.price_subtotal / bill.currency_id._get_conversion_rate(self.foreign_currency_id, self.company_currency_id, self.env.user.company_id, bill.invoice_date or datetime.datetime.now())
                        val = {
                            'cost_id': self.id,
                            'product_id': item.product_id.id if item.product_id else False,
                            'name': item.name,
                            'account_id': item.account_id.id,
                            'price_unit': item.balance,#price_unit * (-1 if bill.type_document_id.code == '07' else 1),
                            'foreign_pu': foreign_pu,
                            'split_method': 'by_quantity',
                            'expense_bill_id': bill.id
                        }
                        vals.append(val)
                    else:
                        if not item:
                            raise UserError(_('There is no product selected in the expenses bill %s') %(bill.name))
            for entry in self.expenses_entry_ids:                                                                       
                price_unit = entry.debit
                foreign_pu = entry.amount_currency
                print(_('Journal item product'))
                entry_product = self.env['product.product'].search([('name','=',_('Journal item product'))])
                val = {
                    'cost_id': self.id,
                    'product_id': entry.product_id.id if entry.product_id else entry_product.id,
                    'name': entry.name if entry.product_id else entry.move_id.glosa,
                    'account_id': entry.account_id.id,
                    'price_unit': price_unit,
                    'foreign_pu': foreign_pu,
                    'split_method': 'by_quantity',
                    'expense_bill_id': entry.move_id.id
                }
                vals.append(val)
            self.cost_lines.unlink()
            self.env['stock.landed.cost.lines'].create(vals)
    
    @api.onchange('expenses_bill_ids','expenses_entry_ids')
    def _onchange_expenses_bill_ids(self):
        self._clear_cost_and_valuation_lines()
        if not self.foreign_currency_id and self.expenses_bill_ids and self.expenses_entry_ids:
            raise UserError(_('Please select the foreign currency.'))
        self.get_expenses_from_expense_vendor_and_entry()
        self.get_total_landed_cost()

    def _check_quantity(self):
        inv_qty = 0
        pick_qty = 0
        for inv in self.vendor_bill_ids:
            for iline in inv.invoice_line_ids:
                if iline.product_id.type != 'service':
                    inv_qty += iline.product_uom_id._compute_quantity(iline.quantity, iline.product_id.product_tmpl_id.uom_id, rounding_method='HALF-UP') if iline.product_id.type != 'service' else 0
            for pick in inv.picking_ids:
                for pline in pick.move_ids_without_package:
                    pick_qty += pline.quantity_done
        if inv_qty != pick_qty:
            raise UserError(_('Quantities in invoices are not the same than quantities in invoice pickins.'))
    
    def _clear_cost_and_valuation_lines(self):
        self.cost_lines = False
        self.valuation_adjustment_lines = False

    @api.onchange('vendor_bill_ids')
    def _onchange_vendor_bill_ids(self):
        if not self.foreign_currency_id and self.vendor_bill_ids:
            raise UserError(_('Please select the foreign currency.'))
        self._clear_cost_and_valuation_lines()
        picking_ids = []
        product_ids = []
        total = total_signed = quantity = 0
        for inv in self.vendor_bill_ids:
            if not inv.picking_ids:
                raise UserError(_('There is no pickings on this invoice %s.') %inv.name)
            for pick in inv.picking_ids:
                pick._onchange_invoice_id()
            total += sum(line.price_subtotal if line.product_id.type != 'service' else 0 for line in inv.invoice_line_ids)  #inv.amount_untaxed
            total_signed += abs(sum(line.price_subtotal * (line.tc if not inv.transit_move_line_id else inv.transit_move_line_id.tc) if line.product_id.type != 'service' else 0 for line in inv.invoice_line_ids)) #abs(inv.amount_untaxed_signed)
            # total_exp += sum(line.price_subtotal if line.product_id.type == 'service' else 0 for line in inv.invoice_line_ids)  #inv.amount_untaxed
            # total_exp_signed += abs(sum(line.price_subtotal * line.tc if line.product_id.type == 'service' else 0 for line in inv.invoice_line_ids)) #abs(inv.amount_untaxed_signed)
            if not self.foreign_currency_id:
                self.foreign_currency_id = inv.currency_id
            for picking in inv.picking_ids:
                picking_ids.append(picking.id) 
            for line in inv.invoice_line_ids:
                quantity += line.product_uom_id._compute_quantity(line.quantity, line.product_id.product_tmpl_id.uom_id, rounding_method='HALF-UP') if line.product_id.type != 'service' else 0 #line.quantity if line.product_id.type != 'service' else 0
                if line.product_id.id not in product_ids and not self.many_products and line.product_id.type != 'service':
                    product_ids.append(line.product_id.id)
                    if len(product_ids) > 1:
                        self.many_products = True
                        self.product_id = False
                    else:
                        self.many_products = False
                        self.product_id = line.product_id
                else:
                    product_ids.append(line.product_id.id)
                    if len(product_ids) < 2:
                        self.many_products = False
        self._check_quantity()
        self.total_quantity = quantity
        self.amount_total_vendor = total
        self.amount_total_vendor_signed = total_signed
        # Gastos si existieran en las facturas
        self.get_expenses_from_expense_vendor_and_entry()
        # self.amount_total_expenses += total_exp
        # self.amount_total_expenses_signed += total_exp_signed
        self.picking_ids = [(6, 0, picking_ids)]
        self.get_total_landed_cost()
        if len(self.vendor_bill_ids) > 0:
            if self.many_products:
                self.env.user.notify_warning(_('This landed cost form will have more than one product'))
            else:
                self.env.user.notify_info(_('This landed cost form will have only one product'))
            # return {
            #     'type': 'ir.actions.client',
            #     'tag': 'display_notification',
            #     'params': {
            #         'title': _('Landed Cost Warning!'),
            #         'message': _('This landed cost form will have more than one product'),
            #         'sticky': False,
            #     }
            # }
            # return {
            #     'warning': {
            #         'title': _('Landed Cost Warning!'),
            #         'message': _('This landed cost form will have more than one product')}
            #     }

    def get_expenses_from_expense_vendor_and_entry(self):
        total = total_signed = 0
        for inv in self.expenses_bill_ids:
            if not self.foreign_currency_id:
                raise UserError(_('First select the foreign currency'))
            if inv.type == 'in_refund':
                sign = -1
            else:
                sign = 1
            if self.foreign_currency_id != inv.currency_id:
                if inv.tc_per:
                    total += inv.amount_untaxed / inv.currency_rate * sign
                else:
                    total += inv.amount_untaxed / inv.currency_id._get_conversion_rate(self.foreign_currency_id, inv.currency_id, self.company_id, inv.invoice_date or datetime.datetime.now()) * sign
                total_signed += abs(inv.amount_untaxed_signed) * sign
            else:
                total += inv.amount_untaxed * sign
                total_signed += abs(inv.amount_untaxed_signed) * sign
        self.amount_total_expenses = total
        self.amount_total_expenses_signed = total_signed
        total_exp = total_exp_signed = 0
        for inv in self.vendor_bill_ids:
            total_exp += sum(line.price_subtotal if line.product_id.type == 'service' else 0 for line in inv.invoice_line_ids)  #inv.amount_untaxed
            total_exp_signed += abs(sum(line.price_subtotal * line.tc if line.product_id.type == 'service' else 0 for line in inv.invoice_line_ids)) #abs(inv.amount_untaxed_signed)
        for entry in self.expenses_entry_ids:
            total_exp += entry.amount_currency
            total_exp_signed += entry.debit
        self.amount_total_expenses += total_exp
        self.amount_total_expenses_signed += total_exp_signed

    def get_total_landed_cost(self):
        self.amount_total_landed = self.amount_total_vendor + self.amount_total_expenses
        self.amount_total_landed_signed = self.amount_total_vendor_signed + self.amount_total_expenses_signed
        if self.total_quantity > 0:
            self.unit_cost = self.amount_total_landed / self.total_quantity
            self.unit_cost_signed = self.amount_total_landed_signed / self.total_quantity
        else:
            self.unit_cost = 0
            self.unit_cost_signed = 0

    #TODO modificar para el nuevo modelo desde la funcion heredada
    def compute_landed_cost(self):
        res = super(LandedCost, self).compute_landed_cost()
        vals = []
        for valuation in self.valuation_adjustment_lines:
            eb_id = valuation.cost_line_id.expense_bill_id
            # if eb_id.currency_id != self.env.user.company_id.currency_id:
            valuation.additional_landed_cost_foreign = valuation.additional_landed_cost / eb_id.currency_rate if eb_id else 1
            # else:
            #     valuation.additional_landed_cost_foreign = valuation.additional_landed_cost / eb_id.currency_id._get_conversion_rate(self.foreign_currency_id, self.company_currency_id, self.env.user.company_id, eb_id.invoice_date or  datetime.datetime.now())
        product_ids = []
        for pick in self.picking_ids:
            for line in pick.move_ids_without_package:
                if line.product_id.id not in product_ids:
                    product_ids.append(line.product_id.id)
        for product_id in product_ids:
            # total_qty = sum(self.env['account.move.line'].search([('move_id','=', self.vendor_bill_ids.ids)]).filtered(lambda v: v.product_id.id == product_id).mapped('quantity'))
            product = self.env['product.product'].search([('id','=',product_id)])
            inv_qty = 0
            for iline in self.vendor_bill_ids.invoice_line_ids:
                if iline.product_id == product:
                    inv_qty += iline.product_uom_id._compute_quantity(iline.quantity, iline.product_id.product_tmpl_id.uom_id, rounding_method='HALF-UP') if iline.product_id.type != 'service' else 0
            val = {
                    'landed_id': self.id,
                    'product_id': product_id,
                    'product_qty': inv_qty,
                    'uom_id': product.product_tmpl_id.uom_id.id,
            }
            self.env['data.for.report'].search([('landed_id','=',self.id),('product_id','=', product_id)]).unlink()
            dfr = self.env['data.for.report'].create(val)
            for cost in self.cost_lines:
                add_lan_cos = sum(self.env['stock.valuation.adjustment.lines'].search([('cost_line_id','=', cost.id)]).filtered(lambda v: v.product_id.id == product_id).mapped('additional_landed_cost'))
                add_lan_cos_for = sum(self.env['stock.valuation.adjustment.lines'].search([('cost_line_id','=', cost.id)]).filtered(lambda v: v.product_id.id == product_id).mapped('additional_landed_cost_foreign'))
                val = {
                    'data_id': dfr.id,
                    'vendor_bill_id': False,
                    'expense_bill_id': cost.expense_bill_id.id,
                    'additional_landed_cost': add_lan_cos_for,
                    'additional_landed_cost_signed': add_lan_cos,
                }
                vals.append(val)
            for inv in self.vendor_bill_ids:
                if product_id in inv.invoice_line_ids.product_id.ids:
                    total_invoice = sum(self.env['account.move.line'].search([('move_id','=', inv.id)]).filtered(lambda v: v.product_id.id == product_id).mapped('price_subtotal'))
                    if inv.currency_id != inv.company_currency_id:
                        add_lan_cos = total_invoice * inv.currency_rate
                        add_lan_cos_for = total_invoice
                    else:
                        add_lan_cos_for = total_invoice / inv.currency_rate
                        add_lan_cos = total_invoice
                    val = {
                        'data_id': dfr.id,
                        'vendor_bill_id': inv.id,
                        'expense_bill_id': False,
                        'additional_landed_cost': add_lan_cos_for,
                        'additional_landed_cost_signed': add_lan_cos,
                    }
                    vals.append(val)
        self.env['data.for.report.line'].search([('data_id.landed_id','=',self.id)]).unlink()
        self.env['data.for.report.line'].create(vals)
        rec = self.env['data.for.report.line'].search([('data_id.landed_id','=',self.id)])
        return res

class LandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    expense_bill_id = fields.Many2one('account.move', string='Expense Bill')
    foreign_pu = fields.Float(string='Foreign Currency Cost', digits='Product Price')

class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    additional_landed_cost = fields.Float('Additional Landed Cost', digits=(12, 2))
    additional_landed_cost_foreign = fields.Float(string='Foreign Currency Additional Landed Cost', digits=(12, 2))

class DataForReport(models.Model):
    _name = 'data.for.report'
    _description = 'Data For Report'

    landed_id = fields.Many2one('stock.landed.cost', string='Stock Landed Cost')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    product_qty = fields.Float(string='Quantity')
    line_ids = fields.One2many('data.for.report.line', 'data_id', string='Data For Report Line')

class DataForReportLine(models.Model):
    _name = 'data.for.report.line'
    _description = 'Data For Report Line'

    data_id = fields.Many2one('data.for.report', string='Data For Report')
    vendor_bill_id = fields.Many2one('account.move', string='Vendor Bill')
    expense_bill_id = fields.Many2one('account.move', string='Expense Bill')
    expense_entry_id = fields.Many2one('account.move', string='Expense Entry')
    additional_landed_cost = fields.Float(string='Additional Landed Cost', digits=(12, 2))
    additional_landed_cost_signed = fields.Float(string='Additional Landed Cost Signed', digits=(12, 2))