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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    name = fields.Char(string='Mã', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Khách hàng', track_visibility='onchange')
    phone = fields.Char(string='Số điện thoại', related='partner_id.phone', track_visibility='onchange')
    customer_qty = fields.Integer(string='Số lượng khách hàng', default=1)
    user_id = fields.Many2one('res.users', string='Nhân viên chăm sóc', default=lambda self: self._uid)
    time_from = fields.Datetime(string='Từ giờ', copy=False, track_visibility='onchange')
    time_to = fields.Datetime(string='Đến giờ', copy=False, track_visibility='onchange')
    note = fields.Text(string='Ghi chú')
    state = fields.Selection(STATE_BOOKING, default="new", string="Trạng thái", track_visibility='onchange')

    service_ids = fields.Many2many('product.product', string="Dịch vụ")
    product_ids = fields.One2many('service.booking.product', 'service_booking_id', string='Sản phẩm')
    bed_ids = fields.Many2many('service.bed', string='Giường')
    employee_ids = fields.Many2many('hr.employee', string="Nhân viên")
    time = fields.Float(string='Thời lượng', compute='_compute_time', store=True, digits=(16, 2))

    _sql_constraints = [
        ("booking_service_name_unq", "UNIQUE(name)", "Mã đơn đặt dịch vụ phải duy nhất!")
    ]

    @api.one
    @api.depends('time_from', 'time_to')
    def _compute_time(self):
        if self.time_from and self.time_to:
            if int(str(self.time_from)[14:16]) < int(str(self.time_to)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) - 1 + (
                            60 + int(str(self.time_to)[14:16]) - int(str(self.time_from)[14:16])) / 60
            if int(str(self.time_to)[14:16]) >= int(str(self.time_from)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) + (
                            int(str(self.time_to)[14:16]) - int(str(self.time_from)[14:16])) / 60

    @api.onchange('time_from', 'time_to')
    def _onchange_time_from_time_to(self):
        if self.time_from:
            self.time_from = self.time_from.strftime('%Y-%m-%d %H:%M:00')
        if self.time_to:
            self.time_to = self.time_to.strftime('%Y-%m-%d %H:%M:00')
        if self.time_from and self.time_to:
            if self.time_from >= self.time_to:
                self.time_to = False
                return {
                    'warning': {
                        'title': 'Thông báo',
                        'message': '"Từ giờ" phải trước "Đến giờ". Vui lòng chọn lại!'
                    }
                }
            if self.time_from.strftime('%Y-%m-%d') != self.time_to.strftime('%Y-%m-%d'):
                self.time_to = False
                return {
                    'warning': {
                        'title': 'Thông báo',
                        'message': 'Thời gian đặt lịch phải trong một ngày!',
                    }
                }

    @api.model
    def create(self, vals):
        if vals.get("name", "") == "":
            vals['name'] = self.env['ir.sequence'].next_by_code("booking.service.code")
        booking = super(ServiceBooking, self).create(vals)
        booking.validate_bed_state()
        booking.validate_employee_state()
        booking.validate_time_with_service_time()
        return booking

    @api.multi
    def write(self, vals):
        res = super(ServiceBooking, self).write(vals)
        self.validate_bed_state()
        self.validate_employee_state()
        self.validate_time_with_service_time()
        return res

    @api.multi
    def action_confirm(self):
        self.validate_permission()
        self.write({'state': 'confirmed'})

    @api.multi
    def action_working(self):
        self.state = 'working'

    @api.multi
    def action_back_to_new(self):
        self.state = 'new'

    @api.multi
    def action_done(self):
        if self.state == 'done':
            raise except_orm("Thông báo", "Lịch hẹn này đã hoàn thành, vui lòng làm mới lại trình duyệt.")
        self.state = 'done'

    @api.onchange("partner_id")
    def _onchange_partner(self):
        if self.partner_id:
            self.phone = self.partner_id.phone

    def validate_bed_state(self):
        if self.customer_qty != len(self.bed_ids):
            raise except_orm('Cảnh báo', 'Số lượng giường phải bằng số lượng người làm dịch vụ.')
        for bed in self.bed_ids:
            if self.env['service.bed'].get_bed_state(bed.id, self.time_from.strftime('%Y-%m-%d %H:%M:%S'),
                    self.time_to.strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo booking khi giường đang bận')

    def validate_employee_state(self):
        if self.customer_qty != len(self.employee_ids):
            raise except_orm('Cảnh báo', 'Số lượng nhân viên phải bằng số lượng người làm dịch vụ.')
        for employee in self.employee_ids:
            if self.env['hr.employee'].get_employee_state(employee.id, self.time_from.strftime('%Y-%m-%d %H:%M:%S'),
                                                          self.time_to.strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo booking khi nhân viên đang bận')

    def validate_time_with_service_time(self):
        service_time = 0
        time_booking = (self.time_to - self.time_from).seconds / 60
        for service in self.service_ids:
            service_time += service.x_duration
        if service_time > time_booking:
            raise except_orm('Cảnh báo', 'Tổng thời gian làm các dịch vụ phải nhỏ hơn thời gian của booking')

    def validate_permission(self):
        user = self.env.user
        is_sale_man = user.has_group('sales_team.group_sale_salesman')
        is_lead = user.has_group('sales_team.group_sale_salesman_all_leads')
        is_manager = user.has_group('sales_team.group_sale_manager')
        if (is_manager or is_sale_man) and not is_lead:
            raise except_orm('Cảnh báo', 'Bạn không có quyền xác nhận Đơn đặt làm dịch vụ này.')
