# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import except_orm
from odoo.tools import float_round


class PosUseServiceLine(models.Model):
    _name = 'pos.use.service.line'

    name = fields.Char("Name")
    lot_id = fields.Many2one('stock.production.lot', "Lot")
    lot_line_id = fields.Many2one('stock.production.lot.line', "Lot Line")
    service_id = fields.Many2one('product.product', "Service")
    total_count = fields.Float("Total Count")
    paid_count = fields.Float("Paid Count")
    used_count = fields.Float('Used Count')
    qty = fields.Float("Qty", default=1)
    employee_ids = fields.Many2many('hr.employee', 'employee_pos_use_service_line_rel', 'use_service_line_id', 'emp_id', string='Employees')
    price_unit = fields.Float("Price Unit")
    discount = fields.Float("Discount(%)")
    amount = fields.Float("Amount Total", compute="_compute_amount_total", store=True)
    use_service_id = fields.Many2one('pos.use.service', "use Service")
    order_line_id = fields.Many2one('pos.order.line', "Order Line")
    revenue_rate = fields.Float("Revenue Rate")

    @api.onchange('qty','service_id')
    def _product_qty_change(self):
        if not self.use_service_id.pricelist_id:
            raise except_orm('Cảnh báo!', ("Vui lòng chọn bảng giá trước khi tạo bản ghi này!"))
        if not self.service_id:
            return
        product = self.service_id.with_context(
            lang=self.use_service_id.partner_id.lang,
            partner=self.use_service_id.partner_id.id,
            quantity=self.qty,
            date=self.use_service_id.date,
            pricelist=self.use_service_id.pricelist_id.id,
            uom=self.service_id.uom_id.id,
        )
        self.price_unit = product.price


    @api.onchange('service_id', 'price_unit', 'qty')
    def _onchange_discount(self):
        if not self.use_service_id.pricelist_id:
            raise except_orm('Cảnh báo!', ("Vui lòng chọn bảng giá trước khi tạo bản ghi này!"))
        if not (self.service_id and
                self.use_service_id.partner_id and self.use_service_id.pricelist_id and
                self.use_service_id.pricelist_id.discount_policy == 'without_discount'):
            return
        if self.qty < 0:
            raise except_orm('Cảnh báo!', ("Số lượng phải lớn hơn 0. Vui lòng kiểm tra lại"))
        if self.use_service_id.type == 'card':
            if self.lot_id.product_id.product_tmpl_id.x_card_type == 'service_card':
                if self.paid_count - self.used_count < self.qty:
                    raise except_orm('Cảnh báo!', ("Bạn không thể sử dụng nhiều hơn số lần còn lại"))
            if self.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                if self.used_count + self.qty > self.total_count:
                    raise except_orm('Cảnh báo!', ("Bạn không thể sử dụng nhiều hơn số lần còn lại"))
        self.discount = 0.0
        product = self.service_id.with_context(
            lang=self.use_service_id.partner_id.lang,
            partner=self.use_service_id.partner_id.id,
            quantity=self.qty,
            date=self.use_service_id.date,
            pricelist=self.use_service_id.pricelist_id.id,
            uom=self.service_id.uom_id.id,
        )
        product_context = dict(self.env.context, partner_id=self.use_service_id.partner_id.id, date=self.use_service_id.date, uom=self.service_id.uom_id.id)

        price, rule_id = self.use_service_id.pricelist_id.with_context(product_context).get_product_price_rule(self.service_id, self.qty or 1.0,
                                                                                                            self.use_service_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id, self.qty, self.service_id.uom_id,
                                                                                               self.use_service_id.pricelist_id.id)

        if new_list_price != 0:
            if self.use_service_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.use_service_id.pricelist_id.currency_id,
                    self.use_service_id.company_id, self.use_service_id.date or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if discount > 0:
                discount = float_round(discount, precision_rounding=0.01, rounding_method='HALF-UP')
                self.discount = discount

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = None
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(product, qty,
                                                                                                                      self.use_service_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
            if pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        product_currency = product_currency or (product.company_id and product.company_id.currency_id) or self.use_service_id.company_id.currency_id
        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id, self.use_service_id.company_id, self.use_service_id.date)

        return product[field_name] * cur_factor, currency_id

    @api.depends('qty', 'price_unit', 'discount')
    def _compute_amount_total(self):
        for line in self:
            if line.use_service_id.type == 'service':
                line.amount = line.qty * line.price_unit * (1 - (line.discount / 100))
            else:
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                    if line.paid_count < line.used_count + line.qty:
                        line.amount = (line.qty + line.used_count - line.paid_count) * line.price_unit * (1 - (line.discount / 100))