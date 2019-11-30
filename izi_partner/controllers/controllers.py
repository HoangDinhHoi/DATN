# -*- coding: utf-8 -*-
from odoo import http

# class IziPartner(http.Controller):
#     @http.route('/izi_partner/izi_partner/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_partner/izi_partner/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_partner.listing', {
#             'root': '/izi_partner/izi_partner',
#             'objects': http.request.env['izi_partner.izi_partner'].search([]),
#         })

#     @http.route('/izi_partner/izi_partner/objects/<model("izi_partner.izi_partner"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_partner.object', {
#             'object': obj
#         })