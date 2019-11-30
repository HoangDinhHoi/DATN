# -*- coding: utf-8 -*-
from odoo import http

# class IziPosRefund(http.Controller):
#     @http.route('/izi_pos_refund/izi_pos_refund/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_refund/izi_pos_refund/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_refund.listing', {
#             'root': '/izi_pos_refund/izi_pos_refund',
#             'objects': http.request.env['izi_pos_refund.izi_pos_refund'].search([]),
#         })

#     @http.route('/izi_pos_refund/izi_pos_refund/objects/<model("izi_pos_refund.izi_pos_refund"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_refund.object', {
#             'object': obj
#         })