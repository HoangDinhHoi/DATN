# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning as UserError


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_revenue_rate = fields.Float("Revenue Rate")

    @api.onchange('product_id')
    def _onchange_izi_pos_product_id(self):
        list = []
        if self.order_id:
            for item in self.order_id.session_id.config_id.x_category_ids:
                product_ids = self.env['product.product'].search([('pos_categ_id','=', item.id),('active','=', True)])
                for product_id in product_ids:
                    list.append(product_id.id)

        if self.product_id.type == 'bundle':
            if not self.product_id.x_bundle_component_ids: return {'warning': {'title': 'Thông báo', 'message': 'Gói sản phâm %s chưa chọn thành phần!' % (self.product_id.name, )}}
            order_bundle_items = []
            for bundle_component in self.product_id.x_bundle_component_ids:
                if not bundle_component.bundle_option_ids: return {'warning': {'title': 'Thông báo', 'message': 'Thành phần %s của gói sản phâm %s chưa có sản phẩm!' % (bundle_component.name, self.product_id.name, )}}
                if bundle_component.status == 'active':
                    order_bundle_item = {
                        'bundle_component_id': bundle_component.id,
                        'revenue_rate': bundle_component.revenue_rate,
                        'product_id': False,
                        'uom_id': False,
                        'qty': 0,
                        'lot_ids': False,
                    }
                    order_bundle_items.append((0, False, order_bundle_item))
            return {
                'domain': {'product_id': [('id', 'in', list)]},
                'value': {'x_bundle_item_ids': order_bundle_items}
            }
        return {
            'domain': {'product_id': [('id', 'in', list)]}
        }
