# -*- coding: utf-8 -*-
from odoo import http

# class IziBase(http.Controller):
#     @http.route('/izi_base/izi_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_base/izi_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_base.listing', {
#             'root': '/izi_base/izi_base',
#             'objects': http.request.env['izi_base.izi_base'].search([]),
#         })

#     @http.route('/izi_base/izi_base/objects/<model("izi_base.izi_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_base.object', {
#             'object': obj
#         })