# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class StockProductLot(models.Model):
    _inherit = 'stock.production.lot'

    # tính toán số tiền của PMH
    def _compute_amount_coupon(self, amount):
        if self.product_id.x_card_type != 'voucher':
            raise except_orm('Thông báo', ('Mã "%s" không phải là mã của phiếu mua hàng. Vui lòng kiểm tra lại!' % self.name))
        if self.x_state != 'using':
            raise except_orm('Thông báo', ('Mã "%s" hiện không ở trạng thái đang sử dụng. Vui lòng kiểm tra lại!' % self.name))
        if self.product_id.x_card_discount > 0:
            amount_discount = round(amount * self.product_id.x_card_discount / 100, 0)
            if amount_discount < self.product_id.x_card_value:
                if amount_discount < amount:
                    return amount_discount
                else:
                    return amount
        if amount > self.product_id.x_card_value:
            return self.product_id.x_card_value
        return amount

    # lấy các sản phẩm và số lượng thanh toán
    def _get_product_payment(self):
        if self.product_id.x_card_type != 'voucher':
            raise except_orm('Thông báo', ('Mã "%s" không phải là mã của phiếu mua hàng. Vui lòng kiểm tra lại!' % self.name))
        if len(self.product_id.x_product_card_ids) == 0 and len(self.product_id.x_product_category_card_ids):
            return True
        list = []
        for line in self.product_id.x_product_card_ids:
            list.append((line.product_allow_id.id,line.maximum_quantity))
        for line in self.product_id.x_product_category_card_ids:
            product_ids = self.env['product.product'].search([('categ_id','=',line.product_category_allow_id.id)])
            for product_id in product_ids:
                list.append((product_id.id, line.maximum_quantity))
        return list # list các tuple

    # kiem tra phương thuc su dung
    def _check_customer_use_type(self, partner_id):
        if self.x_release_id.use_type == 'fixed':
            if self.x_customer_id.id != partner_id.id:
                raise except_orm('Thông báo', ('PMH có mã "%s" được sử dụng đích danh cho khách hàng khác. Vui lòng kiểm tra lại!' %self.name))
        return True






