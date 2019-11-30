# -*- coding: utf-8 -*-
from odoo import http

# class IziPartnerSource(http.Controller):
#     @http.route('/izi_partner_source/izi_partner_source/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_partner_source/izi_partner_source/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_partner_source.listing', {
#             'root': '/izi_partner_source/izi_partner_source',
#             'objects': http.request.env['izi_partner_source.izi_partner_source'].search([]),
#         })

#     @http.route('/izi_partner_source/izi_partner_source/objects/<model("izi_partner_source.izi_partner_source"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_partner_source.object', {
#             'object': obj
#         })