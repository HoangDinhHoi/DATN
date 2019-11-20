# -*- coding: utf-8 -*-
from odoo import http

# class BsBookingService(http.Controller):
#     @http.route('/bs_booking_service/bs_booking_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bs_booking_service/bs_booking_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bs_booking_service.listing', {
#             'root': '/bs_booking_service/bs_booking_service',
#             'objects': http.request.env['bs_booking_service.bs_booking_service'].search([]),
#         })

#     @http.route('/bs_booking_service/bs_booking_service/objects/<model("bs_booking_service.bs_booking_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bs_booking_service.object', {
#             'object': obj
#         })