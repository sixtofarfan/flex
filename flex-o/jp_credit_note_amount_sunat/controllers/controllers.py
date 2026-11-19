# -*- coding: utf-8 -*-
# from odoo import http


# class JpCreditNoteAmountSunat(http.Controller):
#     @http.route('/jp_credit_note_amount_sunat/jp_credit_note_amount_sunat/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/jp_credit_note_amount_sunat/jp_credit_note_amount_sunat/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('jp_credit_note_amount_sunat.listing', {
#             'root': '/jp_credit_note_amount_sunat/jp_credit_note_amount_sunat',
#             'objects': http.request.env['jp_credit_note_amount_sunat.jp_credit_note_amount_sunat'].search([]),
#         })

#     @http.route('/jp_credit_note_amount_sunat/jp_credit_note_amount_sunat/objects/<model("jp_credit_note_amount_sunat.jp_credit_note_amount_sunat"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('jp_credit_note_amount_sunat.object', {
#             'object': obj
#         })
