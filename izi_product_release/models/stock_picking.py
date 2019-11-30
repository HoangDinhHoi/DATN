# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'
    
    x_product_release_id = fields.Many2one('product.release', string='Product Release')