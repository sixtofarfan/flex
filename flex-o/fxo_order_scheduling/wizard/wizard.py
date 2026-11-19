# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SaleConfirm(models.TransientModel):

    _name = "sale.order.scheduling.wizard"
    _description = "Generate Sale orders"

    name = fields.Date(string='Day')

    def generar_order(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for ids in active_ids:
            line = self.env['sale.order.scheduling.line'].search([
                ('scheduling_id','=',ids),
                ('name','=',self.name)
            ])
            if len(line) == 0:
                raise UserError(_("No hay programación para " + str(self.name)))
            if line.scheduling_id.state == 'draft':
                raise UserError(_("No puede generar pedido de una programacion no confirmada"))

            line.generate_sale_order()
        #return {'type': 'ir.actions.act_window_close'}

class SaleOrderReportWizar(models.TransientModel):

    _name = "order.scheduling.report.wizard"
    _description = "Generate Sale orders"

    name = fields.Date(string='Day')

    def generar_report(self):
        report = self.env['order.scheduling.report'].create({
            'name':self.name,
        })
        order = self.env['sale.order.line'].search([
            ('day_scheduling','=',report.name)
        ])

        for l in order:
            t = self.env['order.scheduling.report.line'].search([
                ('category','=',l.category.id),
                ('name','=',l.type_scheduling),
                ('report_id','=',report.id)
            ])
            if len(t) == 0 :
                self.env['order.scheduling.report.line'].create(
                    {
                        'name':l.type_scheduling,
                        'category':l.category.id,
                        'report_id': report.id
                    }
                )
        report.compute_qty()
        report.set_note()
        report.set_product()
        report_name = 'fxo_order_scheduling.order_scheduling_report'
        action = self.env.ref(report_name).report_action(report.id)
        return action