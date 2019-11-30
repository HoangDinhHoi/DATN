# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_code_search = fields.Char("Code Search")

    @api.multi
    def action_search_code(self):
        if not self.x_code_search:
            return True
        if self.state != 'draft':
            raise except_orm("Thông báo!", ('Đơn hàng khác trạng thái nháp. Bạn không thể tìm kiếm'))
        PosOrderLine_obj = self.env['pos.order.line']
        lot_list = self.x_code_search.split(',')
        for str_lot in lot_list:
            lot_obj = self.env['stock.production.lot'].search([('name', '=', (str_lot.lower().strip())[0] + (str_lot.strip().upper())[1:])])
            if len(lot_obj) == 0:
                lot_obj = self.env['stock.production.lot'].search([('name', '=', str_lot.strip().upper())])
                if len(lot_obj) == 0:
                    raise except_orm('Thông báo', ('Mã "%s" không tồn tại trong hệ thống!' % str_lot.strip()))
            if lot_obj.product_id.type == 'product':
                total_availability = self.env['stock.quant']._get_available_quantity(lot_obj.product_id, self.location_id, lot_id=lot_obj)
                if total_availability <= 0 and lot_obj.product_id.product_tmpl_id.type == 'product':
                    raise except_orm('Thông báo', ('Sản phẩm có số lô/sê-ri "%s" không tồn tại trong địa điểm kho của bạn!' % str_lot.strip()))
            # kiểm tra theo trạng thái thẻ
            if lot_obj.product_id.tracking == 'serial':
                if lot_obj.x_state == 'new':
                    raise except_orm('Thông báo', ('Mã "%s" chưa được kích hoạt!' % str_lot.strip()))
                elif lot_obj.x_state == 'using':
                    raise except_orm('Thông báo', ('Mã "%s" đã bán và đang được sử dụng!' % str_lot.strip()))
                elif lot_obj.x_state == 'used':
                    raise except_orm('Thông báo', ('Mã "%s" đã sử dụng xong!' % str_lot.strip()))
                elif lot_obj.x_state == 'destroy':
                    raise except_orm('Thông báo', ('Mã "%s" đã bị hủy!' % str_lot.strip()))
                else:
                    date_order = self.date_order.utcnow().date()
                    if lot_obj.life_date and lot_obj.life_date + timedelta(days=1) <= date_order:
                        raise except_orm('Thông báo!', (('Mã "%s" hết hạn vào ngày: ' + lot_obj.life_date.strftime("%d-%m-%Y")) % str_lot.strip()))
                # kiem tra xem co nam o don khac
                check_lot = PosOrderLine_obj.search([('x_lot_id', '=', lot_obj.id)])
                if len(check_lot) == 1:
                    raise except_orm('Thông báo!', (('Mã %s đang được gắn ở đơn hàng: ' + str(
                        check_lot[0].order_id.name)) % str_lot.strip()))
            # add vao dong la san pham nhung k co lot
            line_id = False
            if len(self.lines.filtered(lambda item: item.product_id.id == lot_obj.product_id.id and item.x_lot_id.id == False)) > 0:
                for line in self.lines.filtered(lambda item: item.product_id.id == lot_obj.product_id.id and item.x_lot_id.id == False):
                    line.x_lot_id = lot_obj.id
                    line_id = line
                    break
            else:
                if len(self.lines.filtered(
                        lambda item: item.product_id.id == lot_obj.product_id.id and item.x_lot_id.id == lot_obj.id and item.product_id.tracking == 'lot')) > 0:
                    for line in self.lines.filtered(
                            lambda item: item.product_id.id == lot_obj.product_id.id and item.x_lot_id.id == lot_obj.id and item.product_id.tracking == 'lot'):
                        line.qty += 1
                        line._onchange_amount_line_all()
                        break
                else:
                    price_unit = self.pricelist_id.get_product_price(lot_obj.product_id, 1,self.partner_id)
                    count_product_lot = 0
                    if self.x_pos_partner_refund_id:
                        for x in self.statement_ids:
                            if x.x_lot_ids:
                                count_product_lot += 1
                                for y in x.x_lot_ids:
                                    if y.product_id.id == lot_obj.product_id.id:
                                        price_unit = 0
                        if count_product_lot != 0 and price_unit != 0:
                            raise except_orm('Thông báo.', ('Bạn phải trả lại đúng lại voucher mà khách hàng đã dùng để thannh toán trước đó'))
                    argvs = {
                        'product_id': lot_obj.product_id.id,
                        'name': self.name,
                        'price_unit': price_unit,
                        'qty': 1,
                        'discount': 0,
                        'price_subtotal': price_unit,
                        'price_subtotal_incl': price_unit,
                        'x_lot_id': lot_obj.id,
                        'order_id': self.id,
                    }
                    line_id = PosOrderLine_obj.create(argvs)
            if line_id != False:
                argv = {
                    'pos_order_line_id': line_id.id,
                    'lot_name': lot_obj.name,
                }
                self.env['pos.pack.operation.lot'].create(argv)
        self._onchange_amount_all()
        self.x_code_search = False
        # Sangla thêm cập nhật lại revenue khi thêm thẻ hoặc sản phẩm ngày 2/5/2019
        self._action_update_revenue_rate_order_line_multi()

    # them data cho bien tạo account_bank_statement_line
    def _prepare_bank_statement_line_payment_values(self, data):
        args = super(PosOrder, self)._prepare_bank_statement_line_payment_values(data)
        if self._context.get('list_id_coupon', False):
            args['x_lot_ids'] = self._context.get('list_id_coupon', False)
        return args

    def add_payment(self, data):
        if not self.x_pos_partner_refund_id:
            self._check_count_card()
        # for line in self.lines:
        #     # check thêm thực xuất để k phải gắn lot
        #     if line.product_id.tracking != 'none' and not line.x_lot_id and line.qty_export != 0:
        #         raise except_orm('Thông báo.', ('Vui lòng nhập mã lot/serial cho sản phẩm "%s"' % line.product_id.name))
        return super(PosOrder, self).add_payment(data)

    # Sangla thêm cập nhật lại revenue khi thêm thẻ hoặc sản phẩm ngày 2/5/2019
    @api.multi
    def _action_update_revenue_rate_order_line_multi(self):
        total_revenue = 0
        total = 0
        count = len(self.lines)
        print(count)
        for line in self.lines:
            total += line.price_subtotal_incl
        for line in self.lines:
            count -= 1
            if count != 0:
                if total == 0:
                    line.x_revenue_rate = 0
                    total_revenue += 0
                else:
                    line.x_revenue_rate = line.price_subtotal_incl / total
                    total_revenue += line.price_subtotal_incl / total
            else:
                if total == 0:
                    line.x_revenue_rate = 0
                else:
                    line.x_revenue_rate = 1 - total_revenue

    # @api.multi
    # def action_confirm_order(self):
    # HAM NAY DE CAP NHẠT THONG TIN THE DV VA PMH, NHUNG TIENNQ DE SANG MODULE 'izi_pos_customer_confirm'
    #         DE CHINH SUA VIEC BAN NHIEU THE TREN DON HANG. CAP NHAT NGAY 23/05/2019

    def _check_count_card(self):
        x_charge_refund_id = self.env['ir.config_parameter'].get_param('point_of_sale.x_charge_refund_id')
        x_charge_refund = self.env['product.product'].search(
            [('id', '=', x_charge_refund_id)])
        count_e_card = 0
        count_card = 0
        count_service = 0
        count_e_service = 0
        for line in self.lines:
            #cho nay fix cung ma, vi chua co thoi gian nghĩ va lam them giai phap. Tiennq edit
            if line.product_id.default_code == 'e_MH_SPDV':
                count_e_card = count_e_card + 1
                if line.qty != 1:
                    raise except_orm('Thông báo',
                                     'Bạn không thể bán thẻ sản phẩm có số lượng khác 1 trên đơn hàng!')
            if line.product_id.x_card_type in ('service_card','keep_card') and line.product_id.default_code != 'e_MH_SPDV':
                count_card = count_card + 1
                if line.qty != 1:
                    raise except_orm('Thông báo',
                                     'Bạn không thể bán thẻ keep hoặc thẻ dịch vụ có số lượng khác 1 trên đơn hàng!')

            # tạm thời bỏ qua 2 mã để hoàn thành đơn. (DVKHACMENARD, SPKHACMENARD)
            if (line.product_id.default_code not in ('DVKHACMENARD', 'SPKHACMENARD', 'SPBANTANGGIA', 'DVBANTANGGIA') and line.product_id.type == 'service' and line.product_id.x_card_type == 'none' and self.x_type != 'service' and line.product_id.id != x_charge_refund.id):
                if line.product_id.default_code[0:2] == 'e_':
                    count_e_service = count_e_service + 1
                else:
                    count_service = count_service + 1
            for item in line.x_bundle_item_ids:
                if item.product_id.type == 'service':
                    if item.product_id.default_code[0:2] == 'e_':
                        count_e_service = count_e_service + 1
                    else:
                        count_service = count_service + 1
        if count_e_card > count_e_service:
            raise except_orm('Thông báo', 'Số lượng thẻ sản phẩm lớn hơn số lượng dịch vụ sản phẩm. Vui lòng kiểm tra lại!')
        elif count_e_card == 0 and count_e_service != 0:
            raise except_orm('Thông báo', 'Đơn hàng có dịch vụ sản phẩm. Vui lòng gắn thêm thẻ sản phẩm!')
        if count_card > count_service:
            raise except_orm('Thông báo', 'Số lượng thẻ dịch vụ và keep lớn hơn số lượng dịch vụ thường. Vui lòng kiểm tra lại!')
        elif count_card == 0 and count_service != 0:
            raise except_orm('Thông báo', 'Đơn hàng có dịch vụ thường. Vui lòng gắn thêm thẻ dịch vụ hoặc keep!')
        return True
