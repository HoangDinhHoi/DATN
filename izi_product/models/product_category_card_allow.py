# -*- coding: utf-8 -*-
# author: HoiHD
from odoo import fields, models, api, _


# PRODUCT CATEGORY CARD ALLOW
class product_category_card_allow(models.Model):
    _name = 'product.category.card.allow'
    
    product_id = fields.Many2one('product.template', string=_('Product Tempalte'))
    product_category_allow_id = fields.Many2one('product.category', string=_('Product Category'))
    maximum_quantity = fields.Integer(string=_("Maximum Quantity"))