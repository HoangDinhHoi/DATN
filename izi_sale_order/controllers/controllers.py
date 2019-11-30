# -*- coding: utf-8 -*-
from odoo import http

# class IziSaleOrder(http.Controller):
#     @http.route('/izi_sale_order/izi_sale_order/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_sale_order/izi_sale_order/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_sale_order.listing', {
#             'root': '/izi_sale_order/izi_sale_order',
#             'objects': http.request.env['izi_sale_order.izi_sale_order'].search([]),
#         })

#     @http.route('/izi_sale_order/izi_sale_order/objects/<model("izi_sale_order.izi_sale_order"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_sale_order.object', {
#             'object': obj
#         })