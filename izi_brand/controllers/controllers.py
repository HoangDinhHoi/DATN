# -*- coding: utf-8 -*-
from odoo import http

# class IziBrand(http.Controller):
#     @http.route('/izi_brand/izi_brand/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_brand/izi_brand/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_brand.listing', {
#             'root': '/izi_brand/izi_brand',
#             'objects': http.request.env['izi_brand.izi_brand'].search([]),
#         })

#     @http.route('/izi_brand/izi_brand/objects/<model("izi_brand.izi_brand"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_brand.object', {
#             'object': obj
#         })