# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InheritCrmContact(models.Model):
    _inherit = 'crm.contact'

    crm_lead_ids = fields.One2many('crm.lead', 'contact_id', string='CRM Leads')
