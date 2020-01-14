# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class InheritPosUseService(models.Model):
    _inherit = 'pos.use.service'

    origin = fields.Char(string='Origin')

    @api.model
    def create(self, vals):
        res = super(InheritPosUseService, self).create(vals)
        name = 'DV' + res.company_id.partner_id.x_partner_old_code if res.company_id.partner_id.x_partner_old_code else 'DV' + res.company_id.partner_id.x_partner_code
        sequence = self.env['ir.sequence'].next_by_code('pos.use.service') or _('New')
        res.name = name + '/' + sequence[6:]

        # check lại origin để xem có  là thu hồi thẻ khi làm booking hay không. nếu có găn lại để tham chiếu
        if res.origin:
            service_booking = self.env['service.booking'].search([('name', '=', res.origin)])
            if len(service_booking) == 1:
                #kiểm tra dịch vụ trong booking và dịch vụ làm sử dụng thẻ
                for i in res.use_service_ids:
                    if i.service_id.id not in service_booking.services.ids:
                        raise except_orm('Thông báo!', ('Dịch vụ %s không có trong Đơn đặt làm dịch vụ') % (i.service_id.default_code))
                    if i.employee_ids:
                        for emp in i.employee_ids:
                            if emp.id not in service_booking.employees.ids:
                                raise except_orm('Thông báo!', ('Nhân viên %s không có trong Đơn đặt làm dịch vụ') % (emp.x_employee_code))
            service_booking.use_service_id = res.id
        return res

    # @api.multi
    # def action_search_serial(self):
    #     res = super(InheritPosUseService, self).action_search_serial()
    #     if self.origin:
    #         service_booking = self.env['service.booking'].search([('name', '=', self.origin)])
    #         if len(service_booking) == 1:
    #             #kiểm tra dịch vụ trong booking và dịch vụ làm sử dụng thẻ
    #             for i in self.use_service_ids:
    #                 if i.service_id.id not in service_booking.services.ids:
    #                     raise except_orm('Thông báo!', ('Dịch vụ %s không có trong Đơn đặt làm dịch vụ') % (i.service_id.default_code))
    #                 if i.employee_ids:
    #                     for emp in i.employee_ids:
    #                         if emp.id not in service_booking.employees.ids:
    #                             raise except_orm('Thông báo!', ('Nhân viên %s không có trong Đơn đặt làm dịch vụ') % (emp.x_employee_code))
    #         service_booking.use_service_id = self.id

    @api.multi
    def action_confirm(self):
        if self.state != 'draft':
            return True
        if not self.partner_id:
            raise except_orm('Thông báo!', ("Thông tin khách hàng không thể bỏ trống"))
        if not self.pricelist_id:
            raise except_orm('Thông báo!', "Bạn cần điền thông tin bảng giá")
        if not self.company_id:
            raise except_orm('Thông báo!', "Bạn cần điền thông tin công ty")

        if self.origin:
            service_booking = self.env['service.booking'].search([('name', '=', self.origin)])
            if len(service_booking) == 1:
                #kiểm tra dịch vụ trong booking và dịch vụ làm sử dụng thẻ
                for i in self.use_service_ids:
                    if i.service_id.id not in service_booking.services.ids:
                        raise except_orm('Thông báo!', ('Dịch vụ %s không có trong Đơn đặt làm dịch vụ') % (i.service_id.default_code))
                    if i.employee_ids:
                        for emp in i.employee_ids:
                            if emp.id not in service_booking.employees.ids:
                                raise except_orm('Thông báo!', ('Nhân viên %s không có trong Đơn đặt làm dịch vụ') % (emp.x_employee_code))
            service_booking.use_service_id = self.id

        if self.type == 'card':
            return self.action_confirm_card()
        else:
            return self.action_confirm_service()



