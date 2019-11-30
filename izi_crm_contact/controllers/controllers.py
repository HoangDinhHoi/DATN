# -*- coding: utf-8 -*-
from odoo import http

# class IziCrmContact(http.Controller):
#     @http.route('/izi_crm_contact/izi_crm_contact/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm_contact/izi_crm_contact/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm_contact.listing', {
#             'root': '/izi_crm_contact/izi_crm_contact',
#             'objects': http.request.env['izi_crm_contact.izi_crm_contact'].search([]),
#         })

#     @http.route('/izi_crm_contact/izi_crm_contact/objects/<model("izi_crm_contact.izi_crm_contact"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm_contact.object', {
#             'object': obj
#         })