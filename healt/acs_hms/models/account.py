# -*- coding: utf-8 -*-

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    patient_id = fields.Many2one('hms.patient',  string='Patient', index=True, readonly=True, states={'draft': [('readonly', False)]})
    physician_id = fields.Many2one('hms.physician', string='Physician', readonly=True, states={'draft': [('readonly', False)]}) 
    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', readonly=True, states={'draft': [('readonly', False)]})
    appointment_id = fields.Many2one('hms.appointment',  string='Appointment', readonly=True, states={'draft': [('readonly', False)]})
    department_id = fields.Many2one('hr.department', ondelete='restrict', 
        domain=[('patient_depatment', '=', True)], string='Department')

    @api.onchange('patient_id')
    def onchange_patient(self):
        if self.patient_id and not self.partner_id:
        	self.partner_id = self.patient_id.partner_id.id

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    department_id = fields.Many2one(related='move_id.department_id', string='Departamento', store=True, readonly=True)
    patient_id = fields.Many2one(related='move_id.patient_id', string='Patient', store=True, readonly=True)
    physician_id = fields.Many2one(related='move_id.physician_id', string='Physician', store=True, readonly=True)
    ref_physician_id = fields.Many2one(related='move_id.physician_id', string='Referring Physician', store=True, readonly=True)

