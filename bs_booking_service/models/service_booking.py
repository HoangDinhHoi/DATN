# -*- coding: utf-8 -*-
__author__ = "HoiHD"

import logging
from odoo import fields, models, api
from odoo.exceptions import except_orm

_logger = logging.getLogger(__name__)

STATE_BOOKING = [
    ("new", "Mới"), ("confirm", "Xác nhận"), ("order", "Đơn hàng POS"), ("working", "Đang làm"),
    ("done", "Hoàn thành"), ("cancel", "Hủy bỏ"), ("no_sale", "Không bán hàng")
]


class ServiceBooking(models.Model):
    _name = "service.booking"
    _description = "Đặt làm dịch vụ"

    def _default_user(self):
        return self._context.get("uid")

    name = fields.Char(string='Mã')
    partner_id = fields.Many2one('res.partner', string='Khách hàng')
    phone = fields.Char(string='Số điện thoại', related='partner_id.phone')
    customer_qty = fields.Integer(string='Số lượng khách hàng', default=1)
    user_id = fields.Many2one('res.users', string='Nhân viên chăm sóc', default=_default_user)
    time_from = fields.Datetime(string='Từ giờ')
    time_to = fields.Datetime(string='Đến giờ')
    note = fields.Text(string='Ghi chú')
    state = fields.Selection(STATE_BOOKING, default="new", string="Trạng thái")

    service_ids = fields.Many2many('product.product', string="Dịch vụ")
    product_ids = fields.One2many('service.booking.product', 'service_booking_id', string='Sản phẩm')
    bed_ids = fields.Many2many('service.bed', string='Giường')
    employee_ids = fields.Many2many('hr.employee', string="Nhân viên")

    _sql_constraints = [
        ("booking_service_name_unq", "UNIQUE(name)", "Mã đơn đặt dịch vụ phải duy nhất!")
    ]

    @api.model
    def create(self, vals):
        if vals.get("name", "") == "":
            vals['name'] = self.env['ir.sequence'].next_by_code("booking.service.code")
        booking = super(ServiceBooking, self).create(vals)
        booking.validate_bed_state()
        return booking

    @api.multi
    def write(self, vals):
        res = super(ServiceBooking, self).write(vals)
        res.validate_bed_state()
        return res

    @api.onchange("partner_id")
    def _onchange_partner(self):
        if self.partner_id:
            self.phone = self.partner_id.phone

    def validate_bed_state(self):
        if self.customer_qty != len(self.bed_ids):
            raise except_orm('Cảnh báo', 'Số lượng giường phải bằng số lượng người làm booking.')
        for bed in self.bed_ids:
            if self.env['service.bed'].get_bed_state(bed.id, self.time_from.strftime('%Y-%m-%d %H:%M:%S'),
                    self.time_to.strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo booking khi giường đang bận')
