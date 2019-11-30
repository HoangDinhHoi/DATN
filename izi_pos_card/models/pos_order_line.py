# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_lot_id = fields.Many2one('stock.production.lot',"Lot & Serial")
    x_payment_allocation = fields.Float() # phan bo thanh toan cho thanh toan trung
    x_tracking = fields.Char('Product Tracking',compute='_compute_tracking_product')
    # x_amount_promotion = fields.Float('Amount promotion', default=0)

    @api.depends('product_id')
    def _compute_tracking_product(self):
        for item in self:
            item.x_tracking = item.product_id.tracking

    @api.onchange('product_id','x_lot_id')
    def _onchange_lot_and_product(self):
        if self.product_id and self.x_lot_id:
            PosOrderLine_obj = self.env['pos.order.line']
            if self.product_id.tracking == 'none':
                raise except_orm('Thông báo.', ('Sản phẩm "%s" không quản lý theo lot/Serial. Bạn không cần nhập Lot/Serial cho sản phẩm này' %self.product_id.name))
            total_availability = self.env['stock.quant']._get_available_quantity(self.product_id, self.order_id.location_id, lot_id=self.x_lot_id)
            if total_availability <= 0:
                    raise except_orm('Thông báo', ('Sản phẩm có số lô/sê-ri "%s" không tồn tại trong địa điểm kho của bạn!' % self.x_lot_id.name))
            if self.product_id.tracking == 'serial':
                if self.x_lot_id.x_state == 'new':
                    raise except_orm('Thông báo', ('Mã "%s" chưa được kích hoạt!' % self.x_lot_id.name))
                elif self.x_lot_id.x_state == 'using':
                    raise except_orm('Thông báo', ('Mã "%s" đã bán và đang được sử dụng!' % self.x_lot_id.name))
                elif self.x_lot_id.x_state == 'used':
                    raise except_orm('Thông báo', ('Mã "%s" đã sử dụng xong!' % self.x_lot_id.name))
                elif self.x_lot_id.x_state == 'destroy':
                    raise except_orm('Thông báo', ('Mã "%s" đã bị hủy!' % self.x_lot_id.name))
                else:
                    date_order = self.date_order.utcnow().date()
                    if self.x_lot_id.life_date and self.x_lot_id.life_date + timedelta(days=1) <= date_order:
                        raise except_orm('Thông báo!', (('Mã "%s" hết hạn vào ngày: ' + self.x_lot_id.life_date.strftime("%d-%m-%Y")) % self.x_lot_id.name))
                # kiem tra xem co nam o don khac
                check_lot = PosOrderLine_obj.search([('x_lot_id', '=', self.x_lot_id.id)])
                if len(check_lot) == 1:
                    raise except_orm('Thông báo!', (('Mã %s đang được gắn ở đơn hàng: ' + str(
                        check_lot[0].order_id.name)) % self.x_lot_id.name))

