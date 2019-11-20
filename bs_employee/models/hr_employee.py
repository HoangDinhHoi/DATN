# -*- coding: utf-8 -*-
# __author__ = "HoiHD"
from odoo import models, fields, api


class HREmployee(models.Model):
    _inherit = "hr.employee"
    _description = "HR Employee"

    x_employee_code = fields.Char(string="Mã nhân viên")

    _sql_constraints = [
        ("employee_code_unq", "unique(x_employee_code)", "Mã nhân viên phải duy nhất!")
    ]

    @api.model
    def create(self, vals):
        if vals.get("x_employee_code", "") == "":
            vals['x_employee_code'] = self.env['ir.sequence'].next_by_code("employee.code")
        return super(HREmployee, self).create(vals)
