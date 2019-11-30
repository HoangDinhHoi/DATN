# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/19/2019

from odoo import api, fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    x_department_code = fields.Char(string='Code')

    _sql_constraints = [
        ('unique_job', 'unique(x_department_code)', 'Mã phòng ban phải là duy nhất')
    ]
