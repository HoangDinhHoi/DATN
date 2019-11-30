# -*- coding: utf-8 -*-
from odoo import http

# class IziHr(http.Controller):
#     @http.route('/izi_hr/izi_hr/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_hr/izi_hr/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_hr.listing', {
#             'root': '/izi_hr/izi_hr',
#             'objects': http.request.env['izi_hr.izi_hr'].search([]),
#         })

#     @http.route('/izi_hr/izi_hr/objects/<model("izi_hr.izi_hr"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_hr.object', {
#             'object': obj
#         })