# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import RedirectWarning, Warning

class SaleMainParameter(models.Model):
    _inherit = 'sale.main.parameter'

    include_not_invoiced = fields.Boolean(string=u'Considere incluir órdenes de venta aún no facturadas')
    force_limit_fresh_orders = fields.Boolean(string=u'Aplicar el límite de crédito incluso para clientes sin facturas pendientes de pago')
    limit_currency_id = fields.Many2one("res.currency", "Moneda", domain=[('name', 'in', ['PEN', 'USD'])],
                                                       help="""Only currency PEN or USD""")
    invoice_tolerance_due = fields.Integer(u'Días de tolerancia')
    invoice_amount_due = fields.Float(u'Monto mínimo acumulado de facturas vencidas')