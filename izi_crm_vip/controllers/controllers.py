# -*- coding: utf-8 -*-
from odoo import http

# class IziCrmVip(http.Controller):
#     @http.route('/izi_crm_vip/izi_crm_vip/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm_vip/izi_crm_vip/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm_vip.listing', {
#             'root': '/izi_crm_vip/izi_crm_vip',
#             'objects': http.request.env['izi_crm_vip.izi_crm_vip'].search([]),
#         })

#     @http.route('/izi_crm_vip/izi_crm_vip/objects/<model("izi_crm_vip.izi_crm_vip"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm_vip.object', {
#             'object': obj
#         })