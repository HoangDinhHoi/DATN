# -*- coding: utf-8 -*-
from odoo import http

# class IziCrmLead(http.Controller):
#     @http.route('/izi_crm_lead/izi_crm_lead/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm_lead/izi_crm_lead/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm_lead.listing', {
#             'root': '/izi_crm_lead/izi_crm_lead',
#             'objects': http.request.env['izi_crm_lead.izi_crm_lead'].search([]),
#         })

#     @http.route('/izi_crm_lead/izi_crm_lead/objects/<model("izi_crm_lead.izi_crm_lead"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm_lead.object', {
#             'object': obj
#         })