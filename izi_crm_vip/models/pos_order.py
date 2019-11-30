# -*- coding: utf-8 -*-

from odoo import models, fields, api

from calendar import monthrange


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_rank_id = fields.Many2one('crm.customer.rank', "Rank")

    @api.onchange('partner_id')
    def onchange_partner(self):
        self.x_rank_id = self.partner_id.x_rank_id.id if self.partner_id else False

    # Chiết khấu Vip trong đơn hàng
    def action_compute_order_discount(self):
        if self.lines:
            # for line in self.lines:
            #     if line.discount != 0 and not line.x_promotion_reason_id:
            #         line.update({'discount': 0})
            # Lấy thông tin các sản phẩm được giảm giá ngoại lệ theo hạng VIP của KH
            except_dict = {}
            for product in self.partner_id.x_rank_id.except_product_ids:
                except_dict[product.product_id.id] = product.discount
                except_dict['%s_amount' % product.product_id.id] = product.max_amount
            discount_service = self.partner_id.x_rank_id.discount_service
            discount_product = self.partner_id.x_rank_id.discount_product
            discount_except = len(self.partner_id.x_rank_id.except_product_ids)

            for line in self.lines:
                # if line.x_promotion_reason_id:
                #     continue
                if line.product_id.x_card_type != 'none':
                    continue
                if line.price_subtotal_incl == 0:
                    continue
                # Sản phẩm thuộc ngoại lệ
                if discount_except and line.product_id.id in except_dict:
                    key = '%s_amount' % line.product_id.id
                    x_discount = except_dict[line.product_id.id] * (line.price_subtotal_incl) / 100.0
                    if key in except_dict:
                        # Kiểm tra giới hạn số tiền tối đa
                        max_amount = except_dict[key]
                        if max_amount and max_amount < x_discount:
                            x_discount = max_amount
                    # Qui đổi số tiền ra phần trăm
                    line.discount = round(x_discount * 100.0 / (line.price_unit * line.qty), 4)
                # Dịch vụ
                elif discount_service > 0 and line.product_id.type == 'service':
                    line.discount += discount_service
                # Sản phẩm
                elif discount_product > 0 and line.product_id.type == 'product':
                    line.discount += discount_product

    # def add_revenue(self, partner_id, revenue, date_order):
    #     ResPartnerRevenue = self.env['res.partner.revenue']
    #     # Create or update in res_partner_revenue
    #     last_date = monthrange(date_order.year, date_order.month)[1]
    #     date_revenue = date_order.strftime('%Y-%m')
    #     partner_revenue = ResPartnerRevenue.search([('partner_id', '=', partner_id),
    #                                                 ('revenue_date', '>=', date_revenue + '-01'),
    #                                                 ('revenue_date', '<=', date_revenue + '-' + str(last_date))],
    #                                                limit=1)
    #     if partner_revenue:
    #         new_revenue = partner_revenue.revenue + revenue
    #         partner_revenue.write({'revenue': new_revenue,
    #                                'revenue_date': date_order})
    #     else:
    #         ResPartnerRevenue.create({'partner_id': partner_id,
    #                                   'revenue': revenue,
    #                                   'revenue_date': date_order})
    #     self.env['partner.expected.revenue'].add_cumulative_revenue(partner_id)

    # Phát sinh doanh thu
    # @api.multi
    # def action_customer_confirm_order(self):
    #     res = super(PosOrder, self).action_customer_confirm_order()
    #     self.add_revenue(self.partner_id.id, self.x_revenue, self.date_order)
    #     return res

    # xử lý refund
    # @api.multi
    # def done_refund(self):
    #     res = super(PosOrder, self).done_refund()
    #     amount_revenue = self.x_revenue if self.x_revenue < 0 else -self.x_revenue
    #     self.add_revenue(self.partner_id.id, amount_revenue, self.date_order)
    #     return res
