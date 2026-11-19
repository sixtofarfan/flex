# -*- coding: utf-8 -*-

from re import search
from odoo import api, fields, models, _ 
from odoo.exceptions import UserError
from odoo.tools import float_round, float_is_zero

class StockPicking(models.Model):
    _inherit = "stock.picking"

    transit_move_id = fields.Many2one('account.move', string='Transit move')

    def _get_credit_debit_value(self, product, qty):
        for prod_inv in self.invoice_id.invoice_line_ids:
            if product == prod_inv.product_id:
                return prod_inv.price_unit * qty
        raise UserError(_('Some of the products in the picking are not in the invoice selected.'))
    
    def action_done(self):
        res = super(StockPicking, self).action_done()
        # Primero verificamos que sea una compra
        if self.picking_type_id.code == 'incoming' and self.related_location != 'customer':
            # Para crear el asiento de transito
            # Luego verificamos si existen productos cuya categoría tenga
            # configurada una cuenta de transito
            transit_lines = self.move_ids_without_package.filtered(lambda x: x.product_id.product_tmpl_id.categ_id.transit_account)
            if not self.invoice_id and transit_lines:
                raise UserError (_('The picking has products in a category with an account in transit, the invoice to which this picking belongs must be selected.'))
            for move_line in self.move_ids_without_package:
                # Creamos el asiento para mercaderias en transito
                # si la categoria del producto tiene configurada
                # la cuenta de mercadería en transito
                if transit_lines:
                    vals = []
                    val = {
                        'journal_id': move_line.product_id.product_tmpl_id.categ_id.property_stock_journal.id,
                        'date': self.kardex_date,
                        'invoice_date': self.invoice_id.invoice_date,
                        # 'name': _('Accounting entry of goods in transit ' + self.name + ' / ' + move_line.product_id.name),
                        'ref': self.name,
                        'glosa': _('Entry of merchandise to the warehouse %s') %self.invoice_id.import_number,
                    }
                    transit_move = self.env['account.move'].create(val)
                    # Cambiamos el costo de producto para la valorización
                    svl_price = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move_line.id)])
                    #                                                          cantidad a mano  - cantidad de movimiento     *    ultimo precio           +     precio del movimietno  / cantidad a mano     
                    if not float_is_zero(move_line.product_id.last_cost_kardex, precision_digits=8):
                        move_line.product_id.last_cost_kardex = (float_round((move_line.product_id.qty_available - move_line.product_uom_qty) * move_line.product_id.last_cost_kardex,2) + sum(svl_price.mapped('value'))) / move_line.product_id.qty_available if move_line.product_id.qty_available > 0 else 1
                    else:
                        move_line.product_id.last_cost_kardex = sum(svl_price.mapped('value')) / sum(svl_price.mapped('quantity')) if sum(svl_price.mapped('quantity')) > 0 else 1
                    # Creamos las lineas del asiento
                    if move_line.product_id.product_tmpl_id.categ_id.transit_account:
                        for line in move_line.move_line_ids:
                            credit_debit_value = self._get_credit_debit_value(line.product_id, line.qty_done)
                            currency_rate = self.invoice_id.currency_rate if not self.invoice_id.transit_move_line_id else self.invoice_id.transit_move_line_id.move_id.currency_rate
                            val = {
                                'move_id': transit_move.id,
                                'name': _('Goods'),
                                'type_document_id': self.invoice_id.type_document_id.id,
                                'nro_comp': self.invoice_id.ref,
                                'date': self.invoice_id.invoice_date,
                                'date_maturity': self.invoice_id.invoice_date_due,
                                'product_id': line.product_id.id,
                                'quantity': line.qty_done,
                                'product_uom_id': line.product_id.uom_id.id,
                                'ref': self.name,
                                'partner_id': self.partner_id.id,
                                'balance': credit_debit_value * currency_rate, #self.invoice_id.currency_rate,
                                'credit': 0,
                                'debit': credit_debit_value * currency_rate, #self.invoice_id.currency_rate,
                                'account_id': line.product_id.product_tmpl_id.categ_id.property_account_expense_categ_id.id,
                                'journal_id': line.product_id.product_tmpl_id.categ_id.property_stock_journal.id,
                                'currency_id': self.invoice_id.currency_id.id,
                                'company_id': self.invoice_id.company_id.id,
                                'company_currency_id': self.invoice_id.company_currency_id.id,
                                'exchange_rate': currency_rate, #self.invoice_id.currency_rate,
                                'tc': currency_rate, #self.invoice_id.currency_rate,
                                'amount_currency': credit_debit_value,
                                # 'glosa': _('Entry of merchandise to the warehouse %s') %self.invoice_id.import_number,
                            }
                            vals.append(val)
                            val = {
                                'move_id': transit_move.id,
                                'name': _('Goods in transit'),
                                'type_document_id': self.invoice_id.type_document_id.id,
                                'nro_comp': self.invoice_id.ref,
                                'date': self.invoice_id.invoice_date,
                                'date_maturity': self.invoice_id.invoice_date_due,
                                'product_id': line.product_id.id,
                                'quantity': line.qty_done,
                                'product_uom_id': line.product_id.uom_id.id,
                                'ref': self.name,
                                'partner_id': self.partner_id.id,
                                'balance': -credit_debit_value * currency_rate, #self.invoice_id.currency_rate,
                                'credit': credit_debit_value * currency_rate, #self.invoice_id.currency_rate,
                                'debit': 0,
                                'account_id': line.product_id.product_tmpl_id.categ_id.transit_account.id,
                                'journal_id': line.product_id.product_tmpl_id.categ_id.property_stock_journal.id,
                                'currency_id': self.invoice_id.currency_id.id,
                                'company_id': self.invoice_id.company_id.id,
                                'company_currency_id': self.invoice_id.company_currency_id.id,
                                'exchange_rate': currency_rate, #self.invoice_id.currency_rate,
                                'tc': currency_rate, #self.invoice_id.currency_rate,
                                'amount_currency': -credit_debit_value,
                                # 'glosa': _('Entry of merchandise to the warehouse %s') %self.invoice_id.import_number,
                            }
                            vals.append(val)
                    self.env['account.move.line'].create(vals)
                    transit_move.action_post()
                    self.transit_move_id = transit_move
        return res

    # TODO Temporal eliminar funcion luego de corregir   
    def hiden_function_to_reset(self):
        pickings = self.env['stock.picking'].search([('invoice_id.transit_move_line_id', '=', False),('invoice_id.state','=','posted')])
        for pk in pickings:
            transit_move_id = self.env['account.move'].search([('name','ilike',_('Accounting entry of goods in transit')),('ref','=',pk.name),('state','=','posted')])
            if transit_move_id:
                for tm in transit_move_id:
                    tm.with_context(check_move_validity=False).button_draft()
                    for line in tm.line_ids:
                        if pk.invoice_id.currency_id != self.env.company.currency_id:
                            rate = pk.invoice_id.currency_rate if not pk.invoice_id.transit_move_line_id else pk.invoice_id.transit_move_line_id.move_id.currency_rate
                            line.with_context(check_move_validity=False).write({'debit':(abs(line.amount_currency) * rate) if line.amount_currency > 0 else 0})
                            line.with_context(check_move_validity=False).write({'credit':(abs(line.amount_currency) * rate) if line.amount_currency < 0 else 0})
                            line.with_context(check_move_validity=False).write({'balance':abs(line.amount_currency) * rate * (1 if line.debit > 0 else -1)})
                            line.with_context(check_move_validity=False).write({'date': pk.kardex_date})
                            line.with_context(check_move_validity=False).write({'tc': rate})
                    tm.currency_rate = rate
                    tm.date = pk.kardex_date
                    tm.post()
                    pk.transit_move_id = tm

    @api.onchange('kardex_date')
    def _onchange_kardex_date(self):
        for pk in self:
            transit_move_id = self.transit_move_id
            if self.transit_move_id:
                for tm in transit_move_id:
                    transit_move_id.with_context(check_move_validity=False).button_draft()
                    for line in transit_move_id.line_ids:
                        if pk.invoice_id.currency_id != self.env.company.currency_id:
                            rate = pk.invoice_id.currency_rate if not pk.invoice_id.transit_move_line_id else pk.invoice_id.transit_move_line_id.move_id.currency_rate
                            line.debit  = (abs(line.amount_currency) * rate) if line.debit > 0 else 0
                            line.credit = (abs(line.amount_currency) * rate) if line.credit > 0 else 0
                            line.balance = abs(line.amount_currency) * rate * (1 if line.debit > 0 else -1)
                            line.date = pk.kardex_date
                            line.tc = rate
                    transit_move_id.date = pk.kardex_date
                    transit_move_id.post()

    # TODO Temporal eliminar funcion luego de corregir 
    def todas_los_ingresos(self):
        moves = self.env['account.move'].search([('name','ilike',_('Accounting entry of goods in transit')),('state','=','posted')])
        for move in moves:
            # pick = self.env['stock.picking'].search([('invoice_id.transit_move_line_id', '=', False),('invoice_id.state','=','posted')])
            pick = self.env['stock.picking'].search([('name','=',move.ref)])
            # move.button_draft()
            if pick.invoice_id.ref == '9591431345':
                x=1
            for line in move.line_ids:
                line.type_document_id = pick.invoice_id.type_document_id
                line.nro_comp = pick.invoice_id.ref
                line.tc = pick.invoice_id.currency_rate
                line.invoice_date = pick.invoice_id.invoice_date
                line.date_maturity = pick.invoice_id.invoice_date_due
            move.invoice_date = pick.invoice_id.invoice_date
            move.glosa = _('Entry of merchandise to the warehouse %s') %pick.invoice_id.import_number
            # move.post()
