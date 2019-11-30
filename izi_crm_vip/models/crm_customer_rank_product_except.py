# -*- coding: utf-8 -*-
# Created by Hoanglv on 10/25/2019

from odoo import api, fields, models


class CrmCustomerRankProductExcept(models.Model):
    _name = 'crm.customer.rank.product.except'
    _description = 'Customer rank product except'

    product_id = fields.Many2one('product.product', 'Product')
    max_amount = fields.Integer('Maximum amount', help="Maximum amount to discount, left 0 to discount all")
    discount = fields.Float('Discount (%)')
    rank_id = fields.Many2one('crm.customer.rank', 'Rank ID')

    _sql_constraints = [
        ('product_rank_uniq', 'unique(product_id, rank_id)', u'Products list except contains duplicate!')
    ]
