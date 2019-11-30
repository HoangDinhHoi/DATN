# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/19/2019

from odoo import api, fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'

    code = fields.Char(string='Code')

    _sql_constraints = [
        ('unique_job', 'unique(code)', 'Mã công việc phải là duy nhất')
    ]
