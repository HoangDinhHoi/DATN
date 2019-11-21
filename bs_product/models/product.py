# -*- coding: utf-8 -*-
__author__ = "HoiHD"


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_duration = fields.Float(string='Thời lượng', default=0)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', 'Mã sản phẩm phải duy nhất!')]
