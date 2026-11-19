# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class SubscriptionLineUpgrade(models.Model):
    _name = "subscription.line.upgrade"
    _order = 'upgrade_date DESC'

    subscription_id = fields.Many2one('sale.subscription', string='Subscription', ondelete='cascade')
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    subscription_update_line_id = fields.Many2one(comodel_name='sale.subscription.line', string='Linea a Acualizar')
    product_id = fields.Many2one('product.product', required=False, string="Producto")
    name = fields.Char(required=False, string='Descripción')
    uom_id = fields.Many2one('uom.uom', required=False, string='UdM')
    price_unit = fields.Float(string='Precio unitario', required=False, digits=(16, 6))
    quantity = fields.Float(string='Cantidad', required=False)
    price_subtotal = fields.Float(string='Subtotal', required=False)
    price_unit_prev = fields.Float(string='Precio unitario anterior', required=False, digits=(16, 6))
    quantity_prev = fields.Float(string='Cantidad anterior', required=False)
    price_subtotal_prev = fields.Float(string='Subtotal anterior', required=False)
    state = fields.Selection(
        selection=[("done", "Activo"), ("pending", "Pendiente")],
        default="pending", string='Estado')
    invoice_status = fields.Selection(
        selection=[("pending", "Pendiente"), ("invoiced", "Facturado"), ("not_invoiced", "No se Factura")],
        default="pending", string='Facturación')
    service_id = fields.Char(string="Id Servicio")
    upgrade_date = fields.Date(string="Fecha UDT")
    upgrade_temp_finish_date = fields.Date(string="Final Upgrade Temporal")
    stop_date = fields.Date(string="Fecha Finalización")
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company.id)
    from_address = fields.Many2one('res.partner', string='Dirección Anterior')
    current_address = fields.Many2one('res.partner', string='Dirección Traslado')
    type = fields.Selection(
        [
            ("up_same", "Upgrade Solo Mbps"),
            ("up_reduction", "Upgrade Reduccion de Tarifa"),
            ("up_add", "Upgrade Mbps y Renta"),
            ("down_same", "Downgrade Solo Mbps"),
            ("down_reduction", "Downgrade Reduccion de Tarifa"),
            ("down_add", "Downgrade Mbps Renta"),
            ("migration", "Traslado"),
            ("upgrade", "Upgrade"),
            ("upgrade_temp", "Upgrade Temporal"),
            ("downgrade", "Downgrade"),
        ],
        string="Tipo",
    )
    invoice_id = fields.Many2one('account.move', string='Factura')
    user_id = fields.Many2one('res.users', string='Usuario confirma')
    user_approved_id = fields.Many2one('res.users', string='Usuario aprueba')
    user_finish_id = fields.Many2one('res.users', string='Usuario termina')
    date_confirm = fields.Datetime(string='Fecha de Confirmación')
    date_approved = fields.Datetime(string='Fecha de Aprobación')
    date_finish = fields.Datetime(string='Fecha de Terminación')
    is_renovation = fields.Boolean(string='Renovación')
    renovation_type = fields.Selection(
        [
            ("up_same", "Aumento de Mbps"),
            ("up_reduction", "Aumento de Tarifa"),
            ("up_add", "Aumento de Mbps y Tarifa"),
            ("down_same", "Reducción de Mbps"),
            ("down_reduction", "Reducción de Tarifa"),
            ("down_add", "Reducción de Mbps y Tarifa"),
            ("other", "Otro"),
        ],
        string="Tipo Renovación",
    )

    @api.depends('name', 'type', 'upgrade_date', 'sale_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            type = ''
            if (record.type and not record.renovation_type) or (record.type and record.renovation_type):
                if record.type == 'up_same':
                    type = "Upgrade Solo Mbps"
                if record.type == 'up_reduction':
                    type = "Upgrade Reduccion de Tarifa"
                if record.type == 'up_add':
                    type = "Upgrade Mbps y Renta"
                if record.type == 'down_same':
                    type = "Downgrade Solo Mbps"
                if record.type == 'down_reduction':
                    type = "Downgrade Reduccion de Tarifa"
                if record.type == 'down_add':
                    type = "Downgrade Mbps Renta"
                if record.type == 'migration':
                    type = "Traslado"
                if record.type == 'upgrade':
                    type = "Upgrade"
                if record.type == 'upgrade_temp':
                    type = "Upgrade temporal"
                if record.type == 'downgrade':
                    type = "Downgrade"
            if not record.type and record.renovation_type:
                if record.renovation_type == 'up_same':
                    type = "Aumento de Mbps"
                if record.renovation_type == 'up_reduction':
                    type = "Aumento de Tarifa"
                if record.renovation_type == 'up_add':
                    type = "Aumento de Mbps y Tarifa"
                if record.renovation_type == 'down_same':
                    type = "Reducción de Mbps"
                if record.renovation_type == 'down_reduction':
                    type = "Reducción de Tarifa"
                if record.renovation_type == 'down_add':
                    type = "Reducción de Mbps y Tarifa"
                if record.renovation_type == 'other':
                    type = "Otro"
            upgrade_date = str(record.upgrade_date)
            sale_name = record.sale_id.name
            service_id = record.service_id
            name = name + ' / ' + service_id + ' / ' + type + ' / ' + upgrade_date + ' / ' + sale_name
            res.append((record.id, name))
        return res
