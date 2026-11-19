# -*- coding: utf-8 -*-

from odoo import models, fields, api

class WorksheetF2Wizard(models.TransientModel):
    _inherit = 'worksheet.f2.wizard'
    
    def get_window_f2_register(self):
        if self.show_account_entries:
            view = self.env.ref('account_htf2_report.view_f2_register_tree_true').id
        else:
            view = self.env.ref('account_htf2_report.view_f2_register_tree').id
            pivot = self.env.ref('jp_htf2_report_search.view_f2_register_pivot').id
            graph = self.env.ref('jp_htf2_report_search.view_f2_register_graph').id
        return {
            'name': 'Hoja de Trabajo F2 - Registro',
            'type': 'ir.actions.act_window',
            'res_model': 'f2.register',
            'view_mode': 'tree',
            'views': [(view, 'tree'), (pivot, 'pivot'), (graph, 'graph')],
            }
            
    def get_window_f2_balance(self):
        view = self.env.ref('account_htf2_report.view_f2_balance_tree').id
        pivot = self.env.ref('jp_htf2_report_search.view_f2_balance_pivot').id
        graph = self.env.ref('jp_htf2_report_search.view_f2_balance_graph').id
        return {
            'name': 'Hoja de Trabajo F2 - Balance',
            'type': 'ir.actions.act_window',
            'res_model': 'f2.balance',
            'view_mode': 'tree',
            'views': [(view, 'tree'), (pivot, 'pivot'), (graph, 'graph')],
            }