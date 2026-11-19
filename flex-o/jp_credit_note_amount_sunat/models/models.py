# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class jp_credit_note_amount_sunat(models.Model):
#     _name = 'jp_credit_note_amount_sunat.jp_credit_note_amount_sunat'
#     _description = 'jp_credit_note_amount_sunat.jp_credit_note_amount_sunat'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
