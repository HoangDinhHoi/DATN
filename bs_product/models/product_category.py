# -*- coding: utf-8 -*-
__author__ = "HoiHD"


from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    x_code = fields.Char(string="Mã", default="/")

    _sql_constraints = [
        ("product_category_x_code_unq", "UNIQUE(x_code)", "Mã nhóm sản phẩm phải duy nhất!")
    ]
