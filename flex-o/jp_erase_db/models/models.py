# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class erase_db(models.Model):
    _name = 'erase.db'
    _description = 'Erase Database'

    name = fields.Char('Name')
    data = fields.Text(string='Data')

    def erase_data(self):
        return {
            'name': _('Erase Data'),
            'res_model': 'erase.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('jp_erase_db.view_erase_wizard_form').id,
            'target': 'new',
            'type': 'ir.actions.act_window', 
        }

class erase_wizard(models.TransientModel):
    _name = 'erase.wizard'
    _description = 'Erase Wizard'

    name = fields.Char(string='Name', default='You are one step away from deleting your data from the database !')
    erase_master_data = fields.Boolean(string='Erase master data', help='Master data is very usefull information like partners and products. If you also want to delete these data please thick this checkbox.')
    reset_sequences = fields.Boolean(string='Reset sequences', default=True)

    def erase_date_wizard(self):
        # Check for installed modules
        sale = self.env['ir.module.module'].search([('name', '=', 'sale'),('state', '=', 'installed')])
        purchase = self.env['ir.module.module'].search([('name', '=', 'purchase'),('state', '=', 'installed')])
        bills_of_exchange = self.env['ir.module.module'].search([('name', '=', 'jp_account_bills_of_exchange'),('state', '=', 'installed')])
        stock = self.env['ir.module.module'].search([('name', '=', 'stock'),('state', '=', 'installed')])
        landed_cost = self.env['ir.module.module'].search([('name', '=', 'stock_landed_costs'),('state', '=', 'installed')])
        sql = """  
            delete from account_partial_reconcile;
            delete from account_full_reconcile;
            delete from account_move_line;
            delete from account_move;"""
        if bills_of_exchange:
            sql += """
                delete from account_bill;
                delete from account_bill_form;
                delete from account_refinancing_form;
                delete from interest_late_payment;
                delete from interest_on_refinancing;
                delete from account_send_bank;
                delete from account_protest_payment;
                delete from renew_bill_form;
                delete from account_bank_disbursement;"""
        if stock:
            sql += """
                delete from stock_move;
                delete from stock_move_line;
                delete from stock_valuation_layer;
                delete from stock_valuation_adjustment_lines;
                delete from stock_inventory;
                delete from stock_inventory_line;
                delete from stock_picking;
                delete from stock_quant;"""
        if landed_cost:
            sql += """
                delete from stock_landed_cost;
                delete from stock_landed_cost_lines;"""
        if purchase:
            sql += """
                delete from purchase_order;
                delete from purchase_order_line;
                delete from product_supplierinfo;"""
        if sale:
            sql += """
                delete from sale_order;
                delete from sale_order_line;"""

        if self.erase_master_data:
            sql += """
            delete from product_product;
            delete from product_template;
            delete from res_partner;
            """
        self.env.cr.execute(sql)

        if self.reset_sequences:
            sequences = self.env['ir.sequence'].search([])
            for seq in sequences:
                if seq.date_range_ids:
                    for range in seq.date_range_ids:
                        range.number_next = 1
                else:
                    seq.number_next = 1

        title = _("Erase Data")
        message = _("All data have been erased!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        }