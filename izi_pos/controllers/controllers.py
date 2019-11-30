# -*- coding: utf-8 -*-
from odoo import http

# class IziPos(http.Controller):
#     @http.route('/izi_pos/izi_pos/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos/izi_pos/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos.listing', {
#             'root': '/izi_pos/izi_pos',
#             'objects': http.request.env['izi_pos.izi_pos'].search([]),
#         })

#     @http.route('/izi_pos/izi_pos/objects/<model("izi_pos.izi_pos"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos.object', {
#             'object': obj
#         })