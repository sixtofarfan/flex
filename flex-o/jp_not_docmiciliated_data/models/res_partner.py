# -*- coding: utf-8 -*-
 
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    country_home_nd_jp = fields.Many2one('res.country', string='Country of residence of N.D.')
    v_con_nd_jp = fields.Many2one('table.27', string='Link between the Taxpayer and the Foreign Resident')
    c_d_imp_jp = fields.Many2one('table.25', string='Agreement to Avoid Double Taxation')
    country_home_nd = fields.Char(help='Tabla 35 SUNAT', string='Pais Residencia del N.D.',size=4,related='country_home_nd_jp.table_sunat_35')
    v_con_nd = fields.Char(help='Tabla 27 SUNAT', string='Vinculo entre el Contribuyente y el Residente Extranjero',size=2,related='v_con_nd_jp.code')
    c_d_imp = fields.Char(help='Tabla 25 SUNAT', string='Convenio para Evitar Doble Imposicion',size=2,related='c_d_imp_jp.code')
    
    @api.onchange('country_home_nd')
    def _onchange_country_home_nd(self):
        if self.country_home_nd_jp and not self.country_home_nd_jp.table_sunat_35:
            raise UserError(_('This country does not have any SUNAT code from table 35. Please add a code in countries table!'))