# -*- coding: utf-8 -*-
__author__ = "HoiHD"

import logging
from odoo import models, fields, api
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class HumanResourceEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Khi tạo nhân viên thì đồng thời hệ thống cũng sẽ tự động tạo 1 tài khoản cho nhân viên đó với mật khẩu chính là mã số nhân viên.' \
                   '\nMật khẩu mặc định sẽ là Menard@franchise_ + mã nhân viên.'

    x_employee_code = fields.Char("Employee Code")
    display_name = fields.Char(compute='_compute_display_name', store=True, index=True)
    level_id = fields.Many2one('hr.employee.level', string='Level')

    _sql_constraints = [(
        'x_employee_code_unq', 'unique(x_employee_code)', 'Employee code must be unique!'
    )]

    @api.onchange('x_employee_code')
    def _onchange_x_employee_code(self):
        if self.x_employee_code:
            if ' ' in self.x_employee_code:
                raise ValidationError('Không được để khoảng trống trong mã nhân viên!')
            self.x_employee_code = self.x_employee_code.upper().strip()

    @api.depends('name', 'x_employee_code')
    def _compute_display_name(self):
        for res in self:
            name = res.name
            if res.x_employee_code:
                name = "[%s] %s" % (res.x_employee_code, res.name)
            res.display_name = name

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        result = []
        domain = ['|', '|', ('name', operator, name), ('x_employee_code', operator, name), ('mobile_phone', operator, name)]
        employees = self.search_read(domain, fields=['id', 'x_employee_code', 'name', 'mobile_phone'], limit=limit)
        if employees:
            for employee in employees:
                if employee['mobile_phone']:
                    result.append([employee['id'], "[" + str(employee['x_employee_code']) + "]" + str(employee['name']) + "-" + str(employee['mobile_phone'])])
                else:
                    result.append([employee['id'], "[" + str(employee['x_employee_code']) + "]" + str(employee['name'])])
        return result

    @api.model
    def name_get(self):
        result = []
        for line in self:
            name = line.name or ''
            if line.mobile_phone:
                name = "[" + line.x_employee_code + "]" + ' ' + name + '-' + line.mobile_phone
            else:
                name = "[" + line.x_employee_code + "]" + ' ' + name
            result.append(name)
        return result

    @api.model
    def create(self, vals):
        """
        :param vals:
        :return: thêm 1 fields là người dùng được hệ thống tạo tự động
        """
        res = super(HumanResourceEmployee, self).create(vals)
        if 'user_id' not in vals or not vals['user_id']:
            user_id = res.create_user_from_employee()
            res.update({'user_id': user_id})
        return res

    def create_user_from_employee(self):
        """
            - tạo người dùng hệ thống sau khi tạo nhân viên
            - mật khẩu mặc định: Menard@franchise_ + mã nhân viên
        :return: tài khoản người dùng
        """
        UserIns = self.env['res.users'].sudo()
        default_password = 'Menard@franchise_'+str(self.x_employee_code)

        exist_user = UserIns.search([('login', '=', self.work_email)])
        if exist_user:
            self.constrains_work_mail()

        vals = {
            'login': self.work_email,
            'password': default_password,
            'active': True,
            'company_id': self.company_id.id,
            'company_ids': [(4, self.company_id.id)],
            'image': self.image,
            'name': self.name,
            'email': self.work_email,
            'sel_groups_32_33_34': False,
            'sel_groups_43_44': False,
            'sel_groups_19_22_23': False,
            'sel_groups_28_29': False,
            'sel_groups_56_57': False,
            'sel_groups_71_72': False,
            'sel_groups_54_55': False,
            'sel_groups_59_60': False,
            'sel_groups_2_3': False,
            'sel_groups_1_9_10': 1,
            'phone': self.mobile_phone,
            'mobile': self.mobile_phone
        }
        brand = self.env['res.brand'].search([('code', '=', 'all')])
        res_user_obj = UserIns.with_context(default_employee=True, default_brand_id=brand.id,
                                            x_emp_code=self.x_employee_code).create(vals)
        if res_user_obj:
            return res_user_obj.id

    @api.constrains('work_email')
    def constrains_work_mail(self):
        """
        :return: thông báo nếu email đã tồn tại trong hệ thống
        """
        res_user_obj = self.env['res.users'].sudo()
        hr_employee_obj = self.env['hr.employee'].sudo()
        for line in self:
            if line.work_email:
                user_domain = [('login', '=', line.work_email)]
                if line.user_id:
                    user_domain += [('id', '!=', line.user_id.id)]
                work_email_user = res_user_obj.search(user_domain)
                work_email_employee = hr_employee_obj.search([('work_email', '=', line.work_email), ('id', '!=', line.id)])
                if any([work_email_user, work_email_employee]):
                    raise ValidationError('Địa chỉ email này đã tồn tại!')

    @api.constrains('mobile_phone')
    def constrains_mobile_phone(self):
        """
        :return: thông báo nếu số điện thoại đã tồn tại trong hệ thống
        """
        res_partner_obj = self.env['res.partner'].sudo()
        hr_employee_obj = self.env['hr.employee'].sudo()
        brand = self.env['res.brand'].search([('code', '=', 'all')])
        for line in self:
            if line.mobile_phone:
                mp_partner = res_partner_obj.search(['|', ('phone', '=', line.mobile_phone),
                                                     ('mobile', '=', line.mobile_phone),
                                                     ('brand_id', '=', brand.id if brand else 3)])
                mp_employee = hr_employee_obj.search([('mobile_phone', '=', line.mobile_phone), ('id', 'not in', self.ids)])
                if any([mp_partner, mp_employee]):
                    raise ValidationError('Số điện thoại này đã tồn tại!')
