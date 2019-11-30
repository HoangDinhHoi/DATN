# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/16/2019

from odoo import api, fields, models


class HrEmployeeLevel(models.Model):
    _name = 'hr.employee.level'
    _description = 'Hr employee level'
    _order = 'level'

    name = fields.Char(string='Name')
    level = fields.Char(string='Level')
