# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, exceptions


class GetUpdatePricelistWizard(models.TransientModel):
    _name = "fxo_feasibility.update_pricelist_wzd"

    company_id = fields.Many2one('res.company', 'Compañía', index=True, default=lambda self: self.env.company.id)
    pricelist_id = fields.Many2one('product.pricelist', string="Tarifa")
    type = fields.Selection(selection=[('add_pricelist_manual', 'Adicionar Tarifa Manual'),
                                       ('add_pricelist_automatic',
                                        'Adicionar Tarifa Automática según dirección del Partner')],
                            required=True, string='Seleccione una opción', default='add_pricelist_automatic')

    def update_pricelist_wzd(self):
        active_ids = self.env.context.get('active_ids')
        economic_study = self.env['sale.order.line.qty_street'].search(
            [('id', '=', active_ids), ('company_id', '=', self.company_id.id)])
        for study in economic_study:
            if self.type == 'add_pricelist_manual':
                study.sudo().write({
                    'pricelist_id': self.pricelist_id.id})
            else:
                study.sudo().get_pricelist_id_by_partner()
        return True
