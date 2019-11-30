# -*- coding: utf-8 -*-
__author__ = "HoiHD"

from odoo import fields, models, api
from datetime import datetime
from odoo.tools.config import config
from odoo.exceptions import ValidationError
from odoo.tools import float_round


class RptRevenueProductAndServiceByDate(models.TransientModel):
    _name = 'rpt.pos.revenue.product.and.service.by.date'
    _description = 'Báo cáo doanh thu sản phẩm và dịch vụ theo ngày'

    branch_id = fields.Many2one('res.branch', string='Branch',
                                domain=lambda self: [('id', 'in', self.env.user.branch_ids.ids)])
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    is_export_excel = fields.Boolean(default=False, string='Export to Excel')

    @api.multi
    def get_value_and_product(self, dict_incl_value_after_prlist, total_value_in_bundle, price_unit, total_line, pos_order_product_item_ins):
        """
            tỉ lệ = giá bán / tổng giá bán của các sản phẩm trong gói (qua bảng giá trên đơn POS)
            giá trị của từng sản phẩm trong gói = tỉ lệ x tổng doanh thu của gói
        :param total_value_in_bundle: tổng giá bán của các sản phẩm và dịch vụ trong gói
        :param price_unit: tổng doanh thu của gói
        :param total_line: tổng dòng trong gói
        :param pos_order_product_item_ins: object chứa các sp và dịch vụ
        :return: 1 dictionary chứa id của sản phẩm or dịch vụ và giá trị tương ứng ở trong gói truyền vào
        """
        new_dict = {}
        rate_in_bundle = 0.0
        for line in pos_order_product_item_ins:
            total_line -= 1
            if line.product_id.id in dict_incl_value_after_prlist.keys():
                if total_line != 0:
                    rate_of_product = float_round(dict_incl_value_after_prlist[line.product_id.id]/total_value_in_bundle,
                                                  precision_rounding=0.0001,
                                                  rounding_method='HALF-UP')
                    new_dict.update({
                        line.product_id.id: rate_of_product*price_unit
                    })
                    rate_in_bundle += rate_of_product
                else:
                    new_dict.update({
                        line.product_id.id: (1-rate_in_bundle)*price_unit
                    })
        return new_dict

    @api.multi
    def delete_transient_table(self):
        """
            Xóa các bản ghi đang tồn tại để tạo ra các bản ghi mới
            Mục đích: Tránh để tràn và trùng lặp dữ liệu
        :return: True
        """
        cr = self.env.cr
        cr.execute(""" DELETE FROM revenue_product_and_service_by_date;""")

    @api.multi
    def insert_revenue_product_and_service_into_transient_table(self, order_id, date_order, revenue_by_product, revenue_by_service, other_revenue):
        """
            - Insert dữ liệu sau khi được xử lí và tính toán trong gói
            - Mục đích: để query lấy dữ liệu đổ vào báo cáo
        :param order_id: đơn hàng hiện tại có gói
        :param date_order: ngày đơn hàng
        :param revenue_by_product: doanh thu theo sản phẩm trong gói
        :param revenue_by_service: doanh thu theo dịch vụ trong gói
        :param other_revenue: doanh thu khác (voucher trong gói)
        :return: 1 bản ghi chứa đầy đủ các thông tin trên và nhóm theo ngày đơn hàng or đơn hàng có gói
        """
        cr = self.env.cr
        values = (order_id, date_order, revenue_by_product, revenue_by_service, other_revenue, self.env.uid, datetime.now(), self.env.uid, datetime.now())
        query = """
                    INSERT INTO revenue_product_and_service_by_date 
                    (order_id, date_order, revenue_by_product, revenue_by_service, other_revenue, create_uid, create_date, write_uid, write_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
        cr.execute(query, values)

    @api.multi
    def compute_product_and_service_in_bundle(self):
        """
            - Tìm tất cả các đơn hàng trong pos có các tiêu chí mà người dùng điền vào form với các đơn hàng đã có doanh thu
            - Tìm trong các đơn hàng đó các dòng line có chứa gói mà có doanh thu
            - Dùng các hàm bên trên để tính toán doanh thu theo từng loại
        :return: True
        """
        POSOrder = self.env['pos.order']
        POSOrderLine = self.env['pos.order.line']
        POSOrderProductItem = self.env['pos.order.product.item']
        domain = [('date_order', '>=', datetime(self.date_from.year, self.date_from.month, self.date_from.day, 0, 0, 0)),
                  ('date_order', '<=', datetime(self.date_to.year, self.date_to.month, self.date_to.day, 23, 59, 59)),
                  ('state', 'in', ['paid', 'done', 'invoiced'])]
        if self.branch_id:
            domain += [('branch_id', '=', self.branch_id.id)]

        pos_order_ids = POSOrder.search(domain)
        if len(pos_order_ids) > 0:
            for po in pos_order_ids:
                revenue_by_product = 0
                revenue_by_service = 0
                other_revenue = 0
                pos_order_line_ins = POSOrderLine.search([('order_id', '=', po.id),
                                                          ('product_id.type', '=', 'bundle')])

                if len(pos_order_line_ins) > 0:
                    for pol in pos_order_line_ins:
                        if pol.price_subtotal_incl == 0:
                            continue
                        pos_order_product_item_ins = POSOrderProductItem.search([
                            ('order_line_id', '=', pol.id)
                        ])
                        if len(pos_order_product_item_ins) > 0:
                            total_line = len([r for r in pos_order_product_item_ins])
                            total_value_in_bundle = 0.0
                            #   Dictionary chứa id của sản phẩm và giá của nó sau khi qua bảng giá tại đơn POS
                            dict_incl_value_after_prlist = {}
                            for pins in pos_order_product_item_ins:
                                product = pins.product_id.with_context(
                                    lang=po.partner_id.lang,
                                    partner=po.partner_id,
                                    quantity=pins.qty,
                                    date=po.date_order,
                                    pricelist=po.pricelist_id.id,
                                    uom=pins.uom_id.id
                                )
                                dict_incl_value_after_prlist.update({
                                    pins.product_id.id: (product.price*pins.qty)
                                })
                                total_value_in_bundle += (product.price*pins.qty)
                            value_and_product_dict = self.get_value_and_product(
                                dict_incl_value_after_prlist=dict_incl_value_after_prlist,
                                total_value_in_bundle=total_value_in_bundle,
                                price_unit=pol.x_revenue_rate*po.x_revenue,
                                total_line=total_line,
                                pos_order_product_item_ins=pos_order_product_item_ins)
                            for pi in pos_order_product_item_ins:
                                if pi.product_id.id in value_and_product_dict.keys():
                                    if pi.product_id.type == 'product':
                                        revenue_by_product += value_and_product_dict[pi.product_id.id]
                                    if pi.product_id.type == 'service':
                                        revenue_by_service += value_and_product_dict[pi.product_id.id]
                                    if pi.product_id.type == 'consu':
                                        other_revenue += value_and_product_dict[pi.product_id.id]
                if any([revenue_by_product != 0, revenue_by_service != 0, other_revenue != 0]):
                    # TODO: INSERT data vao 1 bang tam co chua: date_order, doanh_thu_theo_sp, doanh_thu_theo_dich_vu
                    self.insert_revenue_product_and_service_into_transient_table(po.id, po.date_order, revenue_by_product, revenue_by_service, other_revenue)

    @api.multi
    def action_export_report(self):
        """
            - Gọi các hàm bên trên để tính toán
            - xuất báo cáo dưới dạng excel hoặc xem trực tiếp tại giao diện hiện tại
        :return:
        """
        self.delete_transient_table()
        self.compute_product_and_service_in_bundle()
        birt_url = config['birt_url'] or '0'
        if birt_url == '0':
            raise ValidationError('Chưa cấu hình birt_url!')
        report_name = 'rpt_pos_revenue_product_and_service_by_date.rptdesign'
        param_str = {
            '&branch_id': str(self.branch_id.id if self.branch_id else 0),
            '&from_date': self.date_from.strftime('%d/%m/%Y'),
            '&to_date': self.date_to.strftime('%d/%m/%Y')
        }
        birt_link = birt_url + report_name
        if self.is_export_excel:
            birt_link += '&__format=xlsx'
        return {
            "type": "ir.actions.client",
            'name': 'Báo cáo doanh thu sản phẩm và dịch vụ theo ngày',
            'tag': 'BirtViewerActionCurrent',
            'target': 'self',
            'context': {
                'birt_link': birt_link,
                'payload_data': param_str,
            }
        }


class RevenueProductAndServiceByDate(models.TransientModel):
    _name = 'revenue.product.and.service.by.date'
    _description = 'Lưu trữ doanh thu sản phẩm và dịch vụ theo ngày để phục vụ cho việc lấy dữ liệu và đổ vào' \
                   'báo cáo'

    date_order = fields.Date(string='Date Order')
    revenue_by_product = fields.Float(string='Revenue by Product')
    revenue_by_service = fields.Float(string='Revenue by Service')
    order_id = fields.Many2one('pos.order', string='POS Order')
    other_revenue = fields.Float(string='Other Revenue')
