# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/7/2019

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class Serial(models.Model):
    _name = 'crm.lead.serial'

    stock_production_lot_id = fields.Many2one('stock.production.lot', "Stock Production Lot")
    crm_lead_id = fields.Many2one('crm.lead', 'CRM Lead')
