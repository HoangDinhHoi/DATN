# -*- coding: utf-8 -*-
from odoo import http

# class IziCrm(http.Controller):
#     @http.route('/izi_crm/izi_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm/izi_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm.listing', {
#             'root': '/izi_crm/izi_crm',
#             'objects': http.request.env['izi_crm.izi_crm'].search([]),
#         })

#     @http.route('/izi_crm/izi_crm/objects/<model("izi_crm.izi_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm.object', {
#             'object': obj
#         })