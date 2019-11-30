# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosUseService(models.Model):
    _inherit = 'pos.use.service'

    rank_id = fields.Many2one('crm.customer.rank', "Rank")

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.rank_id = self.partner_id.x_rank_id.id

    # Chiết khấu Vip trong đơn hàng
    def action_compute_order_discount(self):
        self.ensure_one()
        if self.use_service_ids:
            for line in self.use_service_ids:
                if line.discount != 0 and not line.promotion_reason_id:
                    line.update({'discount': 0})
            # Lấy thông tin các sản phẩm được giảm giá ngoại lệ theo hạng VIP của KH
            except_dict = {}
            for product in self.partner_id.x_rank_id.except_product_ids:
                except_dict[product.product_id.id] = product.discount
                except_dict['%s_amount' % product.product_id.id] = product.max_amount
            discount_service = self.partner_id.x_rank_id.discount_service
            discount_product = self.partner_id.x_rank_id.discount_product
            discount_except = len(self.partner_id.x_rank_id.except_product_ids)

            for line in self.use_service_ids:
                if line.service_id.x_card_type != 'none':
                    continue
                # Sản phẩm thuộc ngoại lệ
                if discount_except and line.service_id.id in except_dict:
                    key = '%s_amount' % line.service_id.id
                    x_discount = except_dict[line.service_id.id] * (line.price_subtotal_incl) / 100.0
                    if key in except_dict:
                        # Kiểm tra giới hạn số tiền tối đa
                        max_amount = except_dict[key]
                        if max_amount and max_amount < x_discount:
                            x_discount = max_amount
                    # Qui đổi số tiền ra phần trăm
                    line.discount = round(x_discount * 100.0 / (line.price_unit * line.qty), 4)
                # Dịch vụ
                elif discount_service > 0 and line.service_id.type == 'service':
                    line.discount += discount_service
                # Sản phẩm
                elif discount_product > 0 and line.service_id.type == 'product':
                    line.discount += discount_product