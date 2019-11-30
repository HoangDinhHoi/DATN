# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)

STATE_SELECTOR = [('new', 'New'), ('confirmed', 'Confirmed'), ('order', 'Order'), ('working', 'Working'),
                  ('done', 'Done'), ('cancel', 'Canceled'), ('no_sale', 'NoSale')]
DTF = '%Y-%m-%d %H:%M:%S'
DF = '%Y-%m-%d'
DTFR = '%d-%m-%Y %H:%M'


class ServiceBooking(models.Model):
    _name = 'service.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    def _default_company_id(self):
        if self._uid:
            user = self.env['res.users'].search([('id', '=', self._uid)])
            return user.company_id.id

    def _get_employees_domain(self):
        # Lấy ra danh sách nhân viên theo team của nhân viên chăm sóc hiện tại
        employee_ids = self.get_employee_by_team_id(self.env.user.sale_team_id.id)
        return [('id', 'in', employee_ids)]

    def _get_customer_domain(self):
        # Trả lại tập khách hàng thuộc chăm sóc của người dùng hiện tại (không phải quản lý và team lead)
        # Nếu là team lead thì trả lại tập khách hàng của team lead đó chăm sóc
        domain = [('customer', '=', True)]
        if self.type == 'service':
            return domain
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')
        is_lead = self.env.user.has_group('sales_team.group_sale_salesman_all_leads')
        if not is_manager:
            if not is_lead:
                return domain + [('user_id', 'in', self.env.user.sale_team_id.member_ids.ids)]
            return domain + [('user_id', '=', self.env.user.id)]
        return domain

    name = fields.Char(string='Name', track_visibility='onchange')
    type = fields.Selection([('service', 'Service Booking'), ('meeting', 'Customer meeting')], required=True,
                            default='service', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', string="Customer", domain=_get_customer_domain, track_visibility='onchange')
    time_from = fields.Datetime(string="Time From", track_visibility='onchange', copy=False)
    time_to = fields.Datetime(string="Time To", track_visibility='onchange', copy=False)
    company_id = fields.Many2one('res.company', string="Company", default=_default_company_id)
    branch_id = fields.Many2one('res.branch', string="Branch", default=lambda self: self.env.user.sale_team_id.x_branch_id.id)
    team_id = fields.Many2one('crm.team', string="Team", default=lambda self: self.env.user.sale_team_id.id)
    user_id = fields.Many2one('res.users', string="User Responsible", default=lambda self: self._uid,
                              track_visibility='onchange')
    customer_qty = fields.Integer(string="Customer quantity", default=1)
    services = fields.Many2many('product.product', string="Services", domain=[('product_tmpl_id.type', '=', 'service'),
                                                                              '|', ('default_code', 'ilike', 'SPAM'),
                                                                              ('default_code', 'ilike', 'SPAA')])
    employees = fields.Many2many('hr.employee', string="Employees", domain=_get_employees_domain)
    beds = fields.Many2many('crm.team.bed', string='Beds')
    contact_number = fields.Char(string="Contact Number", size=64, track_visibility='onchange')
    note = fields.Text(string="Note")
    is_create_event = fields.Boolean(string='Tạo sự kiện', default=False)
    ref_order_id = fields.Many2one('pos.order', string='Order', track_visibility='onchange')
    ref_sale_order_id = fields.Many2one('sale.order', string='Sale Order', track_visibility='onchange')
    # source_type = fields.Selection([('employee', 'Employee created'), ('customer', 'Customer created')])
    reason_no_sale = fields.Text(string="Reason no sale")
    state = fields.Selection(STATE_SELECTOR, default='new', track_visibility='onchange')
    product_ids = fields.One2many('service.booking.product', 'service_booking_id', string='Products')
    # tham chiếu đơn sử dụng dịch vụ
    use_service_id = fields.Many2one('pos.use.service', string='Use service',track_visibility='onchange')
    time = fields.Float(string='Time', compute='_compute_time', store=True, digits=(16, 2))

    @api.one
    @api.depends('time_from', 'time_to')
    def _compute_time(self):
        if self.time_from and self.time_to:
            if int(str(self.time_from)[14:16]) < int(str(self.time_to)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) - 1 + (60 + int(str(self.time_to)[14:16]) - int(str(self.time_from)[14:16]))/ 60
            if int(str(self.time_to)[14:16]) >= int(str(self.time_from)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) + (int(str(self.time_to)[14:16]) - int(str(self.time_from)[14:16]))/ 60

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.contact_number = self.customer_id.phone

    @api.onchange('time_from', 'time_to')
    def _onchange_time_from_time_to(self):
        if self.time_from:
            self.time_from = self.time_from.strftime('%Y-%m-%d %H:%M:00')
        if self.time_to:
            self.time_to = self.time_to.strftime('%Y-%m-%d %H:%M:00')
        if self.time_from and self.time_to:
            if self.time_from >= self.time_to:
                self.time_to = False
                return {'warning': {'title': _('Thông báo'),
                                    'message': _('"Từ giờ" phải trước "Đến giờ". Vui lòng chọn lại!')}
                        }
            if self.time_from.strftime('%Y-%m-%d') != self.time_to.strftime('%Y-%m-%d'):
                self.time_to = False
                return {'warning': {'title': _('Thông báo'),
                                    'message': _('Thời gian đặt lịch phải trong một ngày!')}
                        }

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id:
            self.team_id = self.user_id.sale_team_id.id

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            employee_ids = self.get_employee_by_team_id(self.team_id.id)
            return {'domain': {'user_id': [('id', 'in', self.team_id.member_ids.ids)],
                               'employees': [('id', 'in', employee_ids)]}}

    @api.model
    def create(self, vals):
        self.validate_time_booking_meeting(vals)
        self.validate_exist_customer_booking_meeting(vals)
        self.validate_product_ids_permission(vals)

        if not vals.get('name', False):
            vals['name'] = self.get_service_booking_name(vals.get('type', 'service'))

        booking = super(ServiceBooking, self).create(vals)
        booking.validate_bed_state()
        booking.validate_employee_state()
        booking.validate_time_with_service_time()
        self.change_lead_state(self._context.get('lead_id', None), vals.get('type', 'meeting'))
        booking.create_event(vals.get('is_create_event', False))
        return booking

    @api.multi
    def write(self, vals):
        self.validate_time_booking_meeting(vals)
        self.validate_product_ids_permission(vals)
        res = super(ServiceBooking, self).write(vals)
        self.validate_bed_state()
        self.validate_employee_state()
        self.validate_time_with_service_time()
        self.create_event(vals.get('is_create_event', False))
        return res

    @api.multi
    def action_confirm(self):
        self.validate_permission()
        if self.type == 'service':
            if len(self.employees) < 1:
                raise except_orm('Thông báo', 'Bạn chưa chọn nhân viên. Vui lòng kiểm tra lại trước khi xác nhận!!!')
            if not self.branch_id:
                raise except_orm('Thông báo', 'Xin mời bạn nhập branch khi xác nhận lịch đặt hẹn!!!')
            if len(self.employees) != self.customer_qty:
                raise except_orm('Thông báo', 'Số lượng nhân viên phải bằng số lượng khách hàng!!!')
            if len(self.services) < 1:
                raise except_orm('Thông báo', 'Bạn chưa chọn dịch vụ. Vui lòng kiểm tra lại trước khi xác nhận!!!')
        self.write({'state': 'confirmed'})

    @api.multi
    def action_working(self):
        self.state = 'working'

    @api.multi
    def action_redeem(self):
        if self.use_service_id and self.use_service_id.state != 'cancel':
            raise except_orm("Thông báo", "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hủy!" %
                             (self.use_service_id.name, self.use_service_id.state))

        view = self.env.ref('izi_pos_use_service.pos_use_service_form')
        return {
            'name': _('Booking to service using'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.use.service',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'context': {
                'readonly_by_pass': True,
                'default_origin': self.name,
                'default_partner_id': self.customer_id.id,
                'default_note': self.name,
            },
        }

    @api.multi
    def action_done(self):
        if self.state == 'done':
            raise except_orm("Thông báo", "Lịch hẹn này đã hoàn thành, vui lòng làm mới lại trình duyệt.")
        if self.type == 'service':
            if not self.use_service_id:
                raise except_orm("Thông báo", "Đơn này chưa thu hồi dịch vụ.")

            if self.use_service_id.state != 'done':
                raise except_orm("Thông báo",
                                 "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hoàn thành!" %
                                 (self.use_service_id.name, self.use_service_id.state))
            if self.use_service_id.pos_order_id:
                self.ref_order_id = self.use_service_id.pos_order_id.id
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        if not self.use_service_id:
            return
        if self.use_service_id.state not in ('done', 'cancel', 'done_refund'):
            raise except_orm("Thông báo", "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hủy!" %
                             (self.use_service_id.name, self.use_service_id.state))
        elif self.use_service_id.state == 'done':
            self.use_service_id.refund()
            self.use_service_id.action_confirm_refund()
            self.use_service_id.action_done_refund()

    @api.multi
    def action_back_to_new(self):
        self.state = 'new'

    @api.multi
    def action_sale_order(self):
        view_id = self.env.ref('sale.view_order_form').id
        sale_order = self.create_sale_order()
        self.write({'state': 'order',
                    'ref_sale_order_id': sale_order.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': sale_order.id
        }

    def validate_permission(self):
        user = self.env.user
        is_sale_man = user.has_group('sales_team.group_sale_salesman')
        is_lead = user.has_group('sales_team.group_sale_salesman_all_leads')
        is_manager = user.has_group('sales_team.group_sale_manager')
        if (is_manager or is_sale_man) and not is_lead:
            raise except_orm('Cảnh báo', 'Bạn không có quyền xác nhận đơn này.')
        if is_lead and self.team_id != user.sale_team_id:
            raise except_orm('Cảnh báo', 'Bạn không có quyền xác nhận đơn của shop khác')

    def get_employee_by_team_id(self, team_id):
        query = '''SELECT he.id 
                    FROM hr_employee he 
                    INNER JOIN res_users ru ON ru.id = he.user_id
                    WHERE ru.sale_team_id = %s'''
        self._cr.execute(query, (team_id, ))
        rows = self._cr.dictfetchall()
        return [r['id'] for r in rows]

    def validate_time_with_service_time(self):
        if self.type == 'meeting':
            return
        service_time = 0
        time_booking = (self.time_to - self.time_from).seconds / 60
        for service in self.services:
            service_time += service.x_duration
        if service_time > time_booking:
            raise except_orm('Cảnh báo', 'Tổng thời gian làm các dịch vụ phải nhỏ hơn thời gian của đơn')

    def get_service_booking_name(self, type):
        seq = 'ev_service_meeting_name_seq'
        if type == 'service':
            seq = 'ev_service_booking_name_seq'
        return self.env['ir.sequence'].with_context(**self._context).next_by_code(seq)

    def change_lead_state(self, lead_id, type='meeting'):
        if not lead_id:
            return
        lead = self.env['crm.lead'].browse(lead_id)
        lead_state = 'booking' if type == 'service' else 'meeting'
        lead.state = lead_state

    def validate_bed_state(self):
        if self.type == 'meeting':
            return
        if self.customer_qty != len(self.beds):
            raise except_orm('Cảnh báo', 'Số lượng giường phải bằng số lượng người làm booking.')
        for bed in self.beds:
            if self.env['crm.team.bed'].get_bed_state(bed.id, self.time_from.strftime('%Y-%m-%d %H:%M:%S'),
                                                      self.time_to.strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo đơn khi giường đang bận')

    def validate_employee_state(self):
        if self.type == 'meeting':
            return
        if self.customer_qty != len(self.employees):
            raise except_orm('Cảnh báo', 'Số lượng nhân viên phải bằng số lượng người làm booking.')
        for employee in self.employees:
            if self.env['hr.employee'].get_employee_state(employee.id, self.time_from.strftime('%Y-%m-%d %H:%M:%S'),
                                                          self.time_to.strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo đơn khi nhân viên đang bận')

    def validate_product_ids_permission(self, vals):
        partner_id = vals.get('customer_id', None) or self.customer_id.id
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        if 'product_ids' in vals and partner.user_id.id != self.env.user.id:
            raise except_orm('Cảnh báo', 'Bạn không thẻ thêm sản phẩm dự kiến cho khách hàng bạn không chăm sóc!')

    def create_sale_order(self):
        order_line = []
        for line in self.product_ids:
            price_unit = self.__get_product_price_unit(self.customer_id, line.product_id)
            order_line.append((0, 0, {'product_id': line.product_id.id,
                                      'name': line.product_id.name,
                                      'price_unit': price_unit,
                                      'product_uom': line.product_id.uom_id.id,
                                      'product_uom_qty': line.qty}))

        vals = {'type': 'retail',
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'branch_id': self.branch_id.id,
                'date_order': self.time_from,
                'partner_id': self.customer_id.id,
                'order_line': order_line}

        return self.env['sale.order'].create(vals)

    @staticmethod
    def __get_product_price_unit(customer, product):
        discount = customer.x_rank_id.discount_service if product.type == 'service' \
            else customer.x_rank_id.discount_product
        price = customer.property_product_pricelist.get_product_price(product, 1, customer)
        return price - ((price * discount) / 100)

    @api.multi
    def action_no_sale(self):
        ctx = {'meeting_id': self.id,
               'customer_id': self.customer_id.id}
        return self.env['confirm.dialog'].with_context(**ctx).get_no_sale_confirm_dialog()

    def validate_time_booking_meeting(self, vals):
        # Thời gian đặt lịch chỉ được trong 1 ngày
        time_from = vals.get('time_from', None) or self.time_from.strftime(DTF)
        time_to = vals.get('time_to', None) or self.time_to.strftime(DTF)
        time_from = (datetime.strptime(time_from, DTF) + relativedelta(hours=7)).strftime(DTFR)
        time_to = (datetime.strptime(time_to, DTF) + relativedelta(hours=7)).strftime(DTFR)
        if time_from[0:4] != time_to[0:4] \
                or time_from[5:7] != time_to[5:7] \
                or time_from[8:10] != time_to[8:10]:
            raise except_orm('Thông báo', 'Thời gian đặt lịch phải trong một ngày!!!')

    def validate_exist_customer_booking_meeting(self, vals):
        """
            Trong 1 ngày 1 khách hàng:
            + Chỉ tồn tại Booking || Meeting
            + Booking/Meeting có thể có nhiều nhưng không được cùng thời điểm
        """
        customer_id = vals.get('customer_id', None) or self.customer_id.id
        time_from = vals.get('time_from', None) or self.time_from.strftime(DTF)
        time_to = vals.get('time_from', None) or self.time_to.strftime(DTF)
        date = datetime.strptime(time_from, DTF).strftime(DF)
        # Chỉ tồn tại Booking || Meeting
        self.validate_exists_one_of_booking_meeting_on_day(vals['type'], customer_id, date)
        # Booking/Meeting có thể có nhiều nhưng không được cùng thời điểm
        self.validate_exists_one_of_booking_meeting_on_time(vals['type'], customer_id, time_from, time_to)

    def validate_exists_one_of_booking_meeting_on_day(self, type, customer_id, date):
        query = '''SELECT name, type FROM service_booking 
                                WHERE customer_id = %s 
                                    AND state != 'cancel'
                                    AND time_from::date = %s'''
        self._cr.execute(query, (customer_id, date))
        res = self._cr.dictfetchone()
        if not res:
            return
        if res['type'] == 'service' and type == 'meeting':
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại booking, vui lòng kiểm tra lại %s' % res['name'])
        if res['type'] == 'meeting' and type == 'service':
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại meeting, vui lòng kiểm tra lại %s' % res['name'])

    def validate_exists_one_of_booking_meeting_on_time(self, type, customer_id, time_from, time_to):
        query = '''SELECT name FROM service_booking 
                        WHERE customer_id = %s 
                            AND type = %s 
                            AND state != 'cancel' 
                            AND ((time_from >= %s AND time_from <= %s) 
                                OR (time_to >= %s AND time_to <= %s) 
                                OR (time_from >= %s AND time_to <= %s))'''
        self._cr.execute(query, (customer_id, type, time_from, time_from, time_to, time_to, time_from, time_to))
        res = self._cr.dictfetchone()
        bm = 'Booking' if type == 'service' else 'Meeting'
        if res:
            raise except_orm('Cảnh báo', 'Đã tồn tại %s cho khách hàng trong khoảng thời gian này: %s' % (bm, res['name']))

    def create_event(self, is_create_event):
        if not is_create_event:
            return
        partner_ids = [self.customer_id.id]
        partner_id = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.id
        partner_ids.append(partner_id)
        name_event = 'Gặp khách hàng'
        if self.type == 'service':
            name_event = 'Làm dịch vụ'
        arg = {
            'name': name_event,
            'start': self.time_from.strftime(DTF),
            'stop': self.time_to.strftime(DTF),
            'allday': False,
            'description': self.note,
            'partner_ids': [(6, 0, partner_ids)],
            'alarm_ids': [(4, 3)],
            'booking_id': self.id,
        }
        self.env['calendar.event'].create(arg)
