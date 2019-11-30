# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    x_code_check = fields.Char('Code')
    x_check_payment_coupon = fields.Boolean(default=False)

    @api.onchange('journal_id')
    def _onchange_check_payment_coupon(self):
        if self.journal_id:
            if self.journal_id.type == 'coupon':
                self.x_check_payment_coupon = True
                self.amount = 0
                return
        self.x_check_payment_coupon = False
        self.amount = self._default_amount()

    @api.onchange('x_code_check')
    def _onchange_code_check(self):
        list_lot = []
        amount_paid = 0
        order_id = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        # danh sách pmh thanh toan chi tiết trước đó
        for line in order_id.statement_ids:
            for item in line.x_lot_ids:
                list_lot.append(item)
            if len(line.x_lot_ids):
                amount_paid += line.amount
        if self.x_code_check:
            list_code = self.x_code_check.split(',')
            # tinh so tien pmh thanh toan k chi tiet
            for code in list_code:
                lot_id = self.env['stock.production.lot'].search([('name', '=', (code.strip().lower()[0] + code.strip().upper()[1:]))], limit=1)
                if lot_id.id == False:
                    raise except_orm('Thông báo', ('Mã "%s" không tồn tại trong hệ thống!' % code))
                lot_id._compute_amount_coupon(self._default_amount()) # chi de kiem tra lot
                lot_id._check_customer_use_type(order_id.partner_id)
                self._check_unique_lot(lot_id)
                list_lot.append(lot_id)
            # tinh so tiền pmh thanh toan
            self.amount = self._check_amount_lot(list_lot, order_id,amount_paid)

    # tính so tien pmh thanh toán chi tiết
    def _check_amount_lot(self, list_lot, order_id,amount_paid):
        amount_total = 0
        amount_default = self._default_amount()
        amount_t = order_id.amount_total
        list_list_product = []
        for lot_id in list_lot:
            list_product = lot_id._get_product_payment()
            if list_product in (True, []): # pmh thanh toan tat ca sp
                amount_total += lot_id._compute_amount_coupon(amount_t)
            else: # pmh thanh toan chi tiet phan nay van loi vi cong vip va ctkm
                amount_order_line = 0
                l_product = []
                l_qty = []
                if len(list_list_product) == 0:
                    list_list_product.append(list_product)
                for item in list_product:
                    l_product.append(item[0])
                    l_qty.append(item[1])
                for line in order_id.lines:
                    if line.product_id.id in l_product:
                        index = l_product.index(line.product_id.id)
                        if l_qty[index] == 0: # k gioi han sl sp
                            amount_line = line.price_subtotal_incl
                        else: #quy dinh sl toi da cho phep thanh toan
                            amount_line = line.price_unit * l_qty[index]
                        if list_product in list_list_product and line.x_payment_allocation >= line.price_subtotal_incl:
                            continue
                        if (line.x_payment_allocation + amount_line) <= line.price_subtotal_incl:
                            amount_order_line += amount_line
                        else:
                            amount_order_line += line.price_subtotal_incl - line.x_payment_allocation
                        line.x_payment_allocation += lot_id._compute_amount_coupon(amount_line)
                        list_list_product.append(list_product)
                amount_total += lot_id._compute_amount_coupon(amount_order_line)

        # tru cac thanh toan truoc do
        amount_total -=  amount_paid
        if amount_total > amount_default:
            return amount_default
        return amount_total

    def _check_unique_lot(self, lot_id):
        query = """SELECT a.stock_production_lot_id 
                    FROM account_bank_statement_line_stock_production_lot_rel a
                    INNER JOIN account_bank_statement_line b on a. account_bank_statement_line_id = b.id
                    INNER JOIN pos_order c on b.pos_statement_id = c.id
                    INNER JOIN stock_production_lot l on a.stock_production_lot_id = l.id
                    WHERE c.state = 'draft'
                    and l.id = %s"""
        self._cr.execute(query,(lot_id.id,))
        res = self._cr.fetchall()
        if any(res) != False:
            raise except_orm('Thông báo', ('Mã "%s" hiện đang được dùng thanh toán ở đơn khác. Vui lòng kiểm tra lại!' % lot_id.name))

    @api.multi
    def check(self):
        order_id = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        if order_id.amount_total >= 0:
            if self.amount < 0:
                raise except_orm('Thông báo', ('Đây không phải là đơn hàng trả lại. Bạn không thể thanh toán âm ở đơn hàng này!'))
            elif self.amount > self._default_amount():
                raise except_orm('Thông báo', ('Số tiền bạn nhập lớn hơn số tiền cần phải thanh toán. Vui lòng kiểm tra lại!'))
        context = dict(self._context or {})
        context['list_id_coupon'] = False
        if self.x_code_check:
            list_id = []
            list_code = self.x_code_check.split(',')
            for i in list_code:
                lot_id = self.env['stock.production.lot'].search([('name', '=', (i.strip().lower()[0] + i.strip().upper()[1:]))], limit=1)
                if lot_id.id == False:
                    raise except_orm('Cảnh báo!', ('Mã "%s" không tồn tại trong hệ thống!' % i.strip().upper()))
                list_id.append(lot_id.id)
            context['list_id_coupon'] = [(6, 0, list_id)]
        return super(PosMakePayment, self.with_context(context)).check()

