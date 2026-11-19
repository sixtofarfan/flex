# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

class AccountBankStatementLine(models.Model):

    _inherit = "account.bank.statement.line"

    type_document_id = fields.Many2one('einvoice.catalog.01', string='Tipo de Documento')
    partner_vat = fields.Char(string='Vat', related='partner_id.vat')

    @api.onchange('ref','type_document_id')
    def _get_ref(self):
        digits_serie = ('').join(self.type_document_id.digits_serie*['0'])
        digits_number = ('').join(self.type_document_id.digits_number*['0'])
        if self.ref:
            if '-' in self.ref:
                partition = self.ref.split('-')
                if len(partition) == 2:
                    if len(partition[1]) > 8 and self.type_document_id.code in ('01','03','04','06','07','08'):
                        if partition[1][:1] == '0':
                            partition[1] = partition[1].lstrip('0')
                        if len(partition[1]) > 8:
                            raise UserError(_('El número de comprobante sin contar la serie no puede tener mas de 8 digitos. El PLE no lo permite.'))
                    serie = digits_serie[:-len(partition[0])] + partition[0]
                    number = digits_number[:-len(partition[1])] + partition[1]
                    self.ref = serie + '-' + number