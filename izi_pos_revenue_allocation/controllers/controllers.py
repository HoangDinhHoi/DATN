# -*- coding: utf-8 -*-
from odoo import http

# class IziPosRevenueAllocation(http.Controller):
#     @http.route('/izi_pos_revenue_allocation/izi_pos_revenue_allocation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_revenue_allocation/izi_pos_revenue_allocation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_revenue_allocation.listing', {
#             'root': '/izi_pos_revenue_allocation/izi_pos_revenue_allocation',
#             'objects': http.request.env['izi_pos_revenue_allocation.izi_pos_revenue_allocation'].search([]),
#         })

#     @http.route('/izi_pos_revenue_allocation/izi_pos_revenue_allocation/objects/<model("izi_pos_revenue_allocation.izi_pos_revenue_allocation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_revenue_allocation.object', {
#             'object': obj
#         })