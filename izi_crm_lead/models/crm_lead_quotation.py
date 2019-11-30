# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/7/2019

from odoo import models, fields


class ProductQuotation(models.Model):
    _name = 'crm.lead.quotation'

    product_id = fields.Many2one('product.product', "Product")
    qty = fields.Integer('Quantity', default=1)
    lead_id = fields.Many2one('crm.lead', 'CRM Lead')

    _sql_constraints = [
        ('check_qty', 'check(qty >= 0)', 'Product quantity greater than 0')
    ]
