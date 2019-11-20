# -*- coding: utf-8 -*-
__author__ = "HoiHD"

import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ServiceBookingProduct(models.Model):
    _name = "service.booking.product"
    _description = "Sản phẩm trong đơn đặt làm dịch vụ"

    product_id = fields.Many2one('product.product', string='Sản phẩm')
    qty = fields.Integer(string='Số lượng', default=1)
    service_booking_id = fields.Many2one('service.booking', string='Đơn đặt làm dịch vụ')
    amount_total = fields.Float(string="Tổng")

    _sql_constraints = [
        ('check_qty', 'check(qty > 0)', 'Số lượng sản phẩm phải lớn hơn 0')
    ]

    @api.onchange('product_id', 'qty')
    def _onchange_product_id_qty(self):
        if not self.service_booking_id.partner_id:
            self.product_id = False
            self.qty = False
            return {
                'warning': {
                    'title': _('Thông báo'),
                    'message': _('Vui lòng chọn khách hàng trước khi chọn sản phẩm!')}
            }

