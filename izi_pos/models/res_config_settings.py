 # -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_charge_refund_id = fields.Many2one('product.product', "Charge Refund", config_parameter='point_of_sale.x_charge_refund_id')
    x_discount_product_id = fields.Many2one('product.product', "Discount Product", config_parameter='point_of_sale.x_discount_product_id')
    x_discount_service_id = fields.Many2one('product.product', "Discount Service", config_parameter='point_of_sale.x_discount_service_id')
