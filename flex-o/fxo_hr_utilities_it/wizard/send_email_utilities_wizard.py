# -*- coding:utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo import api, fields, models
from odoo.exceptions import UserError


class SendEmailUtilitiesWizard(models.TransientModel):
    _name = 'send.email.utilities.wizard'

    @api.model
    def _default_get_template(self):
        template = self.env['mail.template'].search([('model', '=', 'hr.utilities.it.line')], limit=1)
        if template:
            return template.id
        else:
            return False

    line_ids = fields.Many2many('hr.utilities.it.line', 'send_email_utilities_wizard_utility_rel',
                                domain=lambda self: self._get_line_ids_domain())
    template_id = fields.Many2one('mail.template', string='Usar Plantilla',
                                  domain="[('model', '=', 'hr.utilities.it.line')]",
                                  required=True, default=_default_get_template)

    @api.model
    def _get_line_ids_domain(self):
        Utility = self.env['hr.utilities.it'].browse(self._context.get('active_id'))
        if Utility:
            Lines = Utility.utilities_line_ids
            return [('id', 'in', Lines.ids)]
        else:
            return []

    def send_email(self):
        if len(self.line_ids) > 0:
            for line in self.line_ids:
                line.send_email(self.template_id)
            return self.env['popup.it'].get_message('Operación realizada con éxito!')
        else:
            raise UserError("Debe seleccionar al menos un empleado al cual enviarle el correo.")
