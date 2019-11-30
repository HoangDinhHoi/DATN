# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    service_booking_ids = fields.One2many('service.booking', 'ref_sale_order_id', string='Service booking',
                                          ondelete='set null')
