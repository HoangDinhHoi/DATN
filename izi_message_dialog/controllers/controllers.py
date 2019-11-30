# -*- coding: utf-8 -*-
from odoo import http

# class IziMessageDialog(http.Controller):
#     @http.route('/izi_message_dialog/izi_message_dialog/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_message_dialog/izi_message_dialog/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_message_dialog.listing', {
#             'root': '/izi_message_dialog/izi_message_dialog',
#             'objects': http.request.env['izi_message_dialog.izi_message_dialog'].search([]),
#         })

#     @http.route('/izi_message_dialog/izi_message_dialog/objects/<model("izi_message_dialog.izi_message_dialog"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_message_dialog.object', {
#             'object': obj
#         })