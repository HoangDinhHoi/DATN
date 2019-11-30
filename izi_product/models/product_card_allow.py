# -*- coding: utf-8 -*-
# author: HoiHD
from odoo import fields, models, api, _

# PRODUCT CARD ALLOW
class product_card_allow(models.Model):
    _name = 'product.card.allow'
    
    product_id = fields.Many2one('product.template', string=_('Product Tempalte'))
    product_allow_id = fields.Many2one('product.product', string=_('Product'))
    maximum_quantity = fields.Integer(string=_('Maximum Quantity'))