# -*- coding: utf-8 -*-

"""
    Editor: HoiHD
    Date: 15/05/2019 on 14:30 PM
    Description: - Copy lại hàm refund trong module izi_pos_refund
                 - Ghi đè lại hàm đó với mục đích là lấy ra partner trung gian ở account_bank_statement_line ở phương thức thanh toán trung gian
                 - Sau đó cập nhật partner trung gian đó vào account_payment để ghi bút toán cho phương thức thanh toán trung gian
                 - Thêm đối tác trung gian tại dòng 270, 320, 604, 624
                 - Thêm note vào dòng 272, 322
    Đôi nét về tác giả: xem thêm...
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from odoo.tools import float_is_zero
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class PosRefund(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi trạng thái khác tạo mới"))
            if line.state == 'draft' and line.statement_ids:
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi đã có thanh toán"))
            if line.state == 'draft' and self.env.context.get('pos_refund') and line.x_type == 'service':
                raise except_orm("Cảnh báo!", ("Đây là đơn hàng phát sinh từ đơn dịch vụ. Bạn không thể xóa đơn hàng này!"))
        return super(PosRefund, self).unlink()

    @api.multi
    def refund(self):
        if self.env.context.get('pos_refund'):
            if self.x_type == 'service':
                raise except_orm("Cảnh báo!",
                                 ("Đây là đơn hàng phát sinh từ đơn dịch vụ. Bạn không thể refund đơn hàng này!"))
        for line in self.lines:
            if line.product_id.x_card_type == 'voucher':
                if line.x_lot_id.life_date + timedelta(days=1) <= datetime.now().date():
                    raise except_orm('Cảnh báo!',
                                     (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(line.x_lot_id.life_date,
                                                                                        "%Y-%m-%d").strftime(
                                         "%d-%m-%Y") + '. Bạn không thể refund') % line.lot_name.upper().strip()))
                if line.x_lot_id.x_state == 'used':
                    raise except_orm('Cảnh báo!', ("Phiếu mua hàng đã được sử dụng. Bạn không thể refund"))
        if self.x_pos_partner_refund_id:
            raise except_orm('Cảnh báo!', ("Đây là đơn Refund của đơn khác bạn không thể refund được "))
        pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.id)])
        if pos_order_refund:
            raise except_orm('Cảnh báo!', ("Đơn hàng này đã được refund với đơn refund %s" % pos_order_refund.name))
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('user_id', '=', self.env.uid)],
                                                         limit=1)
        if not current_session:
            raise UserError(
                _('To return product(s), you need to open a session that will be used to register the refund.'))
        # Kiểm tra xem khách hàng có đủ điểm đổ để cho khách hàng refun ko
        # if self.x_red_point != 0:
        #     total_point = 0
        #     for point in self.partner_id.x_red_point_ids:
        #         if point.extend_date:
        #             if point.extend_date >= fields.Date.today():
        #                 total_point += point.point - point.used_point
        #         elif point.expire_date and point.expire_date >= fields.Date.today():
        #             total_point += point.point - point.used_point
        #     if total_point < self.x_red_point:
        #         raise except_orm('Thông báo!', ('Số điểm không còn đủ để refund. Vui lòng kiểm tra lại!'))
        """Create a
         copy of order  for refund order"""
        Posorder = self.env['pos.order']
        clone = {
            # ot used, name forced by create
            'name': self.name + _(' RF'),
            'partner_id': self.partner_id.id,
            'company_id': self.env.user.company_id.id,
            'x_rank_id': self.x_rank_id.id,
            'session_id': current_session.id,
            'date_order': fields.Datetime.now(),
            'user_id': self.user_id.id,
            'pos_reference': self.pos_reference,
            'pricelist_id': self.pricelist_id.id,
            'config_id': current_session.config_id.id,
            'state': 'draft',
            'location_id': current_session.config_id.stock_location_id.id,
            'x_pos_partner_refund_id': self.id,
            'x_type': self.x_type,
            'lines': False,
            'amount_tax': -self.amount_tax,
            'amount_total': -self.amount_total,
            'amount_paid': 0,
            # 'x_red_point': -self.x_red_point,
            # 'x_use_red_point': -self.x_use_red_point,
            # 'x_amount_promotion_product': -self.x_amount_promotion_product,
            # 'x_amount_promotion_service': -self.x_amount_promotion_service,
        }
        pos_order_id = Posorder.create(clone)
        pos_order_id.update({'name': 'RF_' + str(self.name)})

        PosorderLine = self.env['pos.order.line']

        x_charge_refund_id = self.env['ir.config_parameter'].get_param('point_of_sale.x_charge_refund_id')
        x_charge_refund = self.env['product.product'].search(
            [('id', '=', x_charge_refund_id)])
        searchconfig_parameter = len(
            self.env['ir.config_parameter'].search([('key', '=', 'point_of_sale.x_charge_refund_id')]))
        if searchconfig_parameter == 0:
            raise ValidationError(
                "Chưa có cầu hình thông số chi phí refund, cần liên hệ quản trị viên")
        # thêm ngược các dòng từ pos_order ban đầu vào đơn refund
        charge_refund = 0
        for line in self.lines:
            if line.product_id.product_tmpl_id.x_card_type != 'voucher':
                qty1 = -line.qty
                if line.product_id.product_tmpl_id.x_card_type != 'none':
                    if current_session.id != self.session_id.id:
                        qty1 = 0
                argvss = {
                    'product_id': line.product_id.id,
                    'name': pos_order_id.name + _(' RF'),
                    'price_unit': line.price_unit,
                    'qty': qty1,
                    # 'qty_export': -line.qty_export,
                    'discount': line.discount,
                    # 'x_amount_promotion': -line.x_amount_promotion,
                    # 'x_promotion_reason_id': line.x_promotion_reason_id.id,
                    'price_subtotal': -line.price_subtotal if qty1 != 0 else 0,
                    'price_subtotal_incl': -line.price_subtotal_incl if qty1 != 0 else 0,
                    'x_lot_id': line.x_lot_id.id,
                    'order_id': pos_order_id.id,
                    # 'x_location_id': line.x_location_id.id,
                }
                pos_order_line_id = PosorderLine.create(argvss)
                # Nếu sản phẩm có lot thì thêm ngược lai lot vô
                if line.x_lot_id:
                    argvs_lot = {
                        'pos_order_line_id': pos_order_line_id.id,
                        'lot_name': line.x_lot_id.name,
                    }
                    pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
            if line.product_id.product_tmpl_id.x_card_type == 'voucher':
                voucher = self._search_voucher(line.x_lot_id.name)
                qty1 = -line.qty
                # if current_session.id != self.session_id.id:
                #     qty1 = 0
                #     charge_refund += (line.price_unit * line.qty - line.x_amount_promotion) * (
                #             1 - (line.discount or 0.0) / 100.0)
                argvss = {
                    'product_id': line.product_id.id,
                    'name': pos_order_id.name + _(' RF'),
                    'price_unit': line.price_unit,
                    'qty': qty1,
                    # 'qty_export': -line.qty_export,
                    'discount': line.discount,
                    # 'x_amount_promotion': -line.x_amount_promotion,
                    # 'x_promotion_reason_id': line.x_promotion_reason_id.id,
                    'price_subtotal': -line.price_subtotal if qty1 != 0 else 0,
                    'price_subtotal_incl': -line.price_subtotal_incl if qty1 != 0 else 0,
                    'x_lot_id': voucher.id,
                    'order_id': pos_order_id.id,
                    # 'x_location_id': line.x_location_id.id,
                }
                pos_order_line_id = PosorderLine.create(argvss)
                # Nếu sản phẩm có lot thì thêm ngược lai lot vô
                if line.x_lot_id:
                    argvs_lot = {
                        'pos_order_line_id': pos_order_line_id.id,
                        'lot_name': voucher.name,
                    }
                    pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
            # Nếu sản phẩm là bunle thì thêm ngược lại
            if line.product_id.type == 'bundle':
                pos_product_item = self.env['pos.order.product.item']
                for tmp in line.x_bundle_item_ids:
                    qty2 = -tmp.qty
                    if tmp.product_id.product_tmpl_id.x_card_type != 'none':
                        if current_session.id != self.session_id.id:
                            qty2 = 0
                    argvs_prodcut_item = {
                        'order_line_id': pos_order_line_id.id,
                        'bundle_component_id': tmp.bundle_component_id.id,
                        'product_id': tmp.product_id.id,
                        'uom_id': tmp.uom_id.id,
                        'qty': qty2,
                        'qty_export': -tmp.qty_export,
                        'tracking_product': tmp.tracking_product,
                    }
                    pos_product_item_id = pos_product_item.create(argvs_prodcut_item)
                    pos_product_item_lot = self.env['pos.order.product.item.lot']
                    for x in tmp.product_item_lot_ids:
                        qty3 = -x.qty
                        if x.product_id.product_tmpl_id.x_card_type != 'none':
                            if current_session.id != self.session_id.id:
                                qty3 = 0
                        argvs_prodcut_item_lot = {
                            'product_item_id': pos_product_item_id.id,
                            'product_id': x.product_id.id,
                            'tracking_product': x.tracking_product,
                            'qty': qty3,
                            'lot_id': x.lot_id.id,
                        }
                        pos_product_item_lot_id = pos_product_item_lot.create(argvs_prodcut_item_lot)
        # thêm dòng phí đổi vào đơn refund
        if current_session.id == self.session_id.id:
            charge_refund = 0
        argvss = {
            'product_id': x_charge_refund.id,
            'name': pos_order_id.name + _(' RF'),
            'price_unit': 1000,
            'qty': -charge_refund / 1000,
            'discount': 0,
            'price_subtotal': -charge_refund,
            'price_subtotal_incl': -charge_refund,
            'lot_name': '',
            'order_id': pos_order_id.id,
        }
        pos_order_line_id = PosorderLine.create(argvss)
        # thêm dịch vụ đã dùng trong thẻ vào order_line
        for line in self.lines:
            if line.product_id.x_card_type == 'service_card' or line.product_id.x_card_type == 'keep_card':
                if line.x_lot_id.life_date + timedelta(days=1) <= fields.Date().today():
                    raise except_orm('Cảnh báo!',
                                     (('Mã "%s" hết hạn vào ngày: ' + line.x_lot_id.life_date.strftime("%d/%m/%Y")) % line.x_lot_id.name))
                for tmp in line.x_lot_id.x_stock_production_lot_line_ids:
                    # lấy giá bán lẻ để refund
                    if not self.pricelist_id:
                        raise UserError(
                            _('You have to select a pricelist in the sale form !\n'
                              'Please set one before choosing a product.'))
                    price = self.pricelist_id.get_product_price(
                        tmp.product_id, tmp.total_count or 1.0, self.partner_id)
                    if tmp.used_count == 0:
                        continue
                    discount = 0
                    argvss = {
                        'product_id': tmp.product_id.id,
                        'name': pos_order_id.name,
                        'price_unit': price,
                        'qty': tmp.used_count,
                        'discount': discount,
                        'price_subtotal': (price * tmp.used_count),
                        'price_subtotal_incl': (price * tmp.used_count),
                        'x_lot_id': '',
                        'order_id': pos_order_id.id,
                    }
                    pos_order_line_id = PosorderLine.create(argvss)
        # Thêm ngược lại các hình thức thanh toán vào đơn hàng refund
        debt_amount = 0
        # x_journal_debit_ids = self.config_id.x_journal_debit_ids.ids if self.config_id.x_journal_debit_ids else False
        # for line in self.statement_ids:
        #     if x_journal_debit_ids and (line.journal_id.id in x_journal_debit_ids):
        #         debt_amount += line.amount
        #   Nếu thanh toán không có ghi nợ
        if debt_amount == 0:
            for line in self.statement_ids:
                tmp = None
                for tmp in current_session.statement_ids:
                    if tmp.journal_id.id == line.journal_id.id:
                        break
                agrsv = {
                    'ref': current_session.name,
                    'name': pos_order_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': tmp.account_id.id,
                    'date': datetime.now().date(),
                    'journal_id': tmp.journal_id.id,
                    'statement_id': tmp.id,
                    'pos_statement_id': pos_order_id.id,
                    'amount': -line.amount,
                    'x_lot_ids': [(4, x.id) for x in line.x_lot_ids],
                    'x_bank_card_id': line.x_bank_card_id.id if line.x_bank_card_id else False,
                    # 'x_ignore_reconcile': line.x_ignore_reconcile,
                    # 'x_intermediary_partner_id': line.x_intermediary_partner_id.id if line.x_intermediary_partner_id.id else False,
                    'branch_id': current_session.branch_id.id
                }
                pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
        # Nếu có thanh toán là ghi nợ
        else:
            for line in self.statement_ids:
                # if x_journal_debit_ids and (line.journal_id.id in x_journal_debit_ids):
                #     continue
                tmp = None
                for tmp in current_session.statement_ids:
                    if tmp.journal_id.id == line.journal_id.id:
                        break
                agrsv = {
                    'ref': current_session.name,
                    'name': pos_order_id.name,
                    'partner_id': self.partner_id.id,
                    'account_id': tmp.account_id.id,
                    'date': datetime.now().date(),
                    'journal_id': tmp.journal_id.id,
                    'statement_id': tmp.id,
                    'pos_statement_id': pos_order_id.id,
                    'amount': -line.amount,
                    'x_lot_ids': [(4, x.id) for x in line.x_lot_ids],
                    'x_bank_card_id': line.x_bank_card_id.id if line.x_bank_card_id else False,
                    # 'x_ignore_reconcile': line.x_ignore_reconcile,
                    'branch_id': current_session.branch_id.id
                }
                pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            # Nếu có thanh toán trong ghi nợ
            invoice_make_payment = self.env['invoice.make.payment'].search([('invoice_id', '=', self.invoice_id.id)])
            if invoice_make_payment:
                for line in invoice_make_payment:
                    tmp = None
                    for tmp in current_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': current_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': tmp.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_lot_ids': False,
                        'x_bank_card_id': line.bank_card_id.id if line.bank_card_id else False,
                        # 'x_ignore_reconcile': True,
                        # 'x_intermediary_partner_id': line.intermediary_partner_id.id if line.intermediary_partner_id.id else False,
                        'branch_id': current_session.branch_id.id,
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            #  so tien con no
            # if self.invoice_id.residual != 0 and x_journal_debit_ids:
            #     for line in x_journal_debit_ids:
            #         tmp = None
            #         for tmp in current_session.statement_ids:
            #             if tmp.journal_id.id == line:
            #                 break
            #         agrsv = {
            #             'ref': current_session.name,
            #             'name': pos_order_id.name,
            #             'partner_id': self.partner_id.id,
            #             'account_id': tmp.account_id.id,
            #             'date': datetime.now().date(),
            #             'journal_id': tmp.journal_id.id,
            #             'statement_id': tmp.id,
            #             'pos_statement_id': pos_order_id.id,
            #             'amount': -self.invoice_id.residual,
            #             'x_lot_ids': False,
            #             'x_bank_card_id': False,
            #             'x_ignore_reconcile': True,
            #             'branch_id': current_session.branch_id.id,
            #         }
            #         pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
        pos_order_id._onchange_amount_all()
        # Return về form của đơn hàng refund
        ctx = self.env.context.copy()
        view = self.env.ref('point_of_sale.view_pos_pos_form')
        if self.env.context.get('pos_refund'):
            return {
                'name': _('Order Refund?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': '',
                'res_id': pos_order_id.id,
                'context': self.env.context,
            }

    @api.multi
    def send_refund(self):
        self.state = 'wait_confirm'
        if len(self.lines) == 0:
            raise except_orm("Cảnh báo!",
                             ('Bạn không thể gửi đơn duyệt refund khi không có dịch vụ hoặc sản phẩm nào!'))
        # for order in self:
        #     for statement in order.statement_ids:
        #         if statement.amount > 0:
        #             raise except_orm("Cảnh báo!", ("Số tiền thanh toán không lớn hơn không trong đơn refund"))
        # self._check_count_card_refund()
        total = 0
        for line in self.statement_ids:
            total += line.amount
        if self.amount_total != total:
            raise except_orm('Cảnh báo!', "Bạn cần thanh toán đủ trước khi gửi refund")
        # Cập nhật lại doanh thu đơn hàng trong đơn refund
        x_journal_loyal_ids = self.config_id.x_journal_loyal_ids.ids if self.config_id.x_journal_loyal_ids else False
        if x_journal_loyal_ids:
            loyal_total = 0.0
            for stt in self.statement_ids:
                if stt.journal_id.id in x_journal_loyal_ids:
                    loyal_total += stt.amount
            # Ghi nhận doanh thu
            if loyal_total < 0:
                self.update({'x_revenue': loyal_total})

        # Nếu trong đơn hàng refund mà trả lại voucher cho khách hàng
        # + Kiểm tra lại xem voucher trả lại cho khách có giống voucher mà khách đã dngf để thanh toán chưa
        if self.session_id.id != self.x_pos_partner_refund_id.session_id.id:
            voucher_dict_payment = {}
            voucher_dict_line = {}
            for line in self.statement_ids:
                for item in line.x_lot_ids:
                    if item.product_id.id not in voucher_dict_payment:
                        voucher_dict_payment[item.product_id.id] = item.product_id.id
                        voucher_dict_payment['%s_amount' % item.product_id.id] = 1
                    else:
                        key = '%s_amount' % item.product_id.id
                        max_amount = voucher_dict_payment[key] + 1
                        voucher_dict_payment['%s_amount' % item.product_id.id] = max_amount
            count = 0
            for line in self.lines:
                if line.product_id.product_tmpl_id.x_card_type == 'voucher':
                    count += 1
                if line.qty != 0 and line.price_unit == 0:
                    if line.product_id.id in voucher_dict_payment:
                        key = '%s_amount' % line.product_id.id
                        amount = voucher_dict_payment[key] - 1
                        voucher_dict_payment['%s_amount' % line.product_id.id] = amount
            if count == 0 and voucher_dict_payment:
                raise except_orm('Thông báo!', ("Bạn phải thêm voucher vào đơn refund, để trả thẻ cho khách hàng."))
            for line in self.lines:
                if line.qty != 0 and line.price_unit == 0:
                    if line.product_id.id in voucher_dict_payment:
                        key = '%s_amount' % line.product_id.id
                        if voucher_dict_payment['%s_amount' % line.product_id.id] != 0:
                            raise except_orm("Thông báo!", ("Bạn phải trả lại thẻ Voucher cho khách hàng!"))

    # Xác nhận đơn hàng refund
    @api.multi
    def confirm_refund(self):
        self.state = 'confirm'

    # Không phê duyệt đơn hàng refund
    @api.multi
    def back_refund(self):
        self.state = 'draft'
        self.update({'x_revenue': 0})

    # check đơn hàng có dịch vụ không
    def check_account_for_coupon_standard_price(self):
        has_service = False
        for line in self.lines:
            if line.product_id.type == 'service' and str(line.product_id.default_code)[:3].upper() == 'SPA':
                has_service = True
        if has_service:
            return 6322  # tai khoan 6322
        else:
            return 6321  # tai khoan 6321

    # Tạo bút toán trích trước giá vốn khi refund đơn
    def _create_refund_credit_move_line(self, pos_oder_line, debit_account, credit_account, name_voucher):
        move_lines = []
        # Giá bán sản phẩm
        cost_price = pos_oder_line.product_id.list_price * 70 / 100 * 20 / 100
        credit_move_vals = {
                'name': 'Trích trước giá vốn ' + str(name_voucher),
                'account_id': credit_account,
                'credit': cost_price,
                'debit': 0.0,
                'partner_id': self.partner_id.id,
                'ref': self.name,
                'branch_id': self.branch_id.id,
                'product_id': pos_oder_line.product_id.id,
                'quantity': 1,
                'date': datetime.strftime(self.date_order,"%Y-%m-%d"),
                # 'company_id': self.company_id.id,
        }
        move_lines.append((0, 0, credit_move_vals))
        dedit_move_vals = {
                'name': 'Trích trước giá vốn ' + str(name_voucher),
                'account_id': debit_account,
                'credit': 0.0,
                'debit': cost_price,
                'partner_id': self.partner_id.id,
                'ref': self.name,
                'branch_id': self.branch_id.id,
                'product_id': pos_oder_line.product_id.id,
                'quantity': 1,
                'date': datetime.strftime(self.date_order,"%Y-%m-%d"),
                # 'company_id': self.company_id.id,
        }
        move_lines.append((0, 0, dedit_move_vals))
        # Tạo bản ghi account.move
        # Cấu hình sổ nhật kí : default : 11 : Hóa đơn nhà cung cấp
        journal_id = self.env['account.journal'].sudo().search([('name', '=', 'Sổ nhật ký khác'), ('company_id', '=', self.env.user.company_id.id)], limit=1)
        move_vals = {
           'ref': self.name,
           'journal_id': journal_id.id,
           'line_ids': move_lines,
           'branch_id': self.branch_id.id,
           'company_id': self.company_id.id,

        }
        move_id = self.env['account.move'].sudo().create(move_vals)
        move_id.post()
        self.write({'move_id': move_id.id})

    # check tài khoản có tồn tại hay không
    def _check_account_exist(self, account):
        if not account:
            except_orm('Thông báo', (
                    'Tài khoản "%s" chưa cấu hình' % account))
        else:
            return account

    # Refund trích trước giá vốn sẩn phẩm < 14% >
    def __create_record_refund_entry_cost_deduction(self):
        # refund thẻ
        # if not self.x_pos_partner_refund_id:
        for line in self.lines:
            if line.product_id.x_card_type == 'voucher':
                if line.product_id.accrued_capital_cost == True:
                    if line.qty > 0:
                        debit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_debt_id.id)
                        credit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_id.id)
                        self._create_refund_credit_move_line(line, debit_account, credit_account, line.x_lot_id.name)
                    else:
                        debit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_id.id)
                        credit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_debt_id.id)
                        self._create_refund_credit_move_line(line, debit_account, credit_account, line.x_lot_id.name)

        for line in self.statement_ids:
            if line.journal_id.type == 'coupon':
                # Lấy voucher
                query = '''SELECT * FROM account_bank_statement_line_stock_production_lot_rel WHERE account_bank_statement_line_id = %s limit 1'''
                self._cr.execute(query, (line.id,))
                production_statement_line_ojb = self._cr.dictfetchone()
                voucher_ojb = self.env['stock.production.lot'].search(
                    [('id', '=', production_statement_line_ojb['stock_production_lot_id'])], limit=1)
                # Tài khoản 1134
                debit_account_ojb = self.env['account.account'].search(
                    [('code', '=', '1134'),
                     ('company_id', '=', self.company_id.id)], limit=1)
                if not debit_account_ojb:
                    raise except_orm('Thông báo', (
                            'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))
                # Tài khoản 6329
                credit_account_ojb = self.env['account.account'].search(
                    [('code', '=', '6329'),
                     ('company_id', '=', self.company_id.id)], limit=1)
                if not credit_account_ojb:
                    raise except_orm('Thông báo', (
                            'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))

                if voucher_ojb.product_id.accrued_capital_cost:
                    if self.session_id.id == self.x_pos_partner_refund_id.session_id.id:
                        credit_account = debit_account_ojb.id
                        debit_account = self.env['account.account'].search(
                            [('code', '=', self.check_account_for_coupon_standard_price()),
                             ('company_id', '=', self.company_id.id)], limit=1)
                        if not debit_account:
                            raise except_orm('Thông báo', (
                                    'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))
                        self._create_refund_credit_move_line(voucher_ojb, debit_account.id, credit_account, voucher_ojb.name)
                    else:
                        # thực hiện 2 bút toán
                        # 1 bút toán hủy thẻ
                        credit_account = debit_account_ojb.id
                        debit_account = self.env['account.account'].search(
                            [('code', '=', self.check_account_for_coupon_standard_price()),
                             ('company_id', '=', self.company_id.id)], limit=1)
                        if not credit_account:
                            raise except_orm('Thông báo', (
                                    'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))
                        self._create_refund_credit_move_line(voucher_ojb, debit_account.id, credit_account, voucher_ojb.name)
                        # 2 bút toán tạo thẻ khác

    # Hoàn thanh đơn refund
    @api.multi
    def done_refund(self):
        if self.state != 'confirm':
            return True
        # Theo cấu hình để cho khách hàng ký xác nhận
        if self.session_id.config_id.module_izi_pos_customer_confirm == True:
            self.state = 'customer_confirm'
        else:
            self.state = 'invoiced'

        # Ghi lịch sử trừ điểm đỏ. hoàn lại điểm đỏ khi refund
        # self.action_red_point_refund()

        # # Cập nhật lại thẻ
        # + Nếu là trong cùng 1 phiên thì cập nhật lại trạng thái thẻ như trước khi bán và nhập lại kho để nhân viên bán lại
        # + Nếu khác phiên thì hủy thẻ và không nhâp lại kho
        self.action_process_card_service()
        # Tạo đơn nhập lại hàng (tạo và done picking)
        self.create_picking()
        # Nếu trong đơn bán bundle có voucher
        self.action_bundle_refund()
        # Xử lý bút toán refund và đóng phiên
        # # Cập nhật lại thanh toán ghi nợ thì không tạo account_move lúc đóng phien
        # self.pos_order_invoice_refund()
        # Ghi ngược lại bút toán chi phí quẹt thẻ nếu trong đơn refund có hình thức là ngân hàng
        for line in self.statement_ids:
            if line.x_bank_card_id and line.journal_id.type == 'bank':
                self._get_move_bank_card(line)
        # Tạo ngược bút toán cho lí do khuyến mại, tạo ra 1 account_move với 1 pos_order
        # Mỗi một dòng line ở pos_order_line sẽ tạo ra 1 account_move_line
        # Bút toán với sổ nhật kí kho
        # Hạch toán từ đầu 641211: về mục có. Đầu 632 về đầu nợ
        # self._get_move_promotion_reason()
        #     Nếu dơn refund bằng tiền vói đơn bán ==> Tạo phân bổ thanh toán ngượi lại so với đơn bán han đầu
        self.action_refund_revenue_allaction()
        #phan bo phan tram doanh thu trong chi tiet donhang
        self._action_update_revenue_rate_order_line_multi()
        #refund trích trước giá vốn của voucher
        self.__create_record_refund_entry_cost_deduction()

    # Xử lý bút toán refund và đóng phiên
    # # Cập nhật lại thanh toán ghi nợ thì không tạo account_move lúc đóng phien
    # def pos_order_invoice_refund(self):
    #     debt_total = 0.0
        # x_journal_debit_ids = self.config_id.x_journal_debit_ids.ids if self.config_id.x_journal_debit_ids else False
        # if x_journal_debit_ids:
        #     for stt in self.statement_ids:
        #         if stt.journal_id.id in x_journal_debit_ids:
        #             debt_total += stt.amount
        # tạo hóa đơn đối với đơn hàng refund
        # if self.amount_total != 0:
        #     self.action_pos_order_invoice()
        #     for line in self.lines:
        #         InvoiceLine = self.env['account.invoice.line']
        #         # Tạo thêm invoice line nếu có triết kkhaau VIP trên đó
        #         if line.product_id.product_tmpl_id.categ_id.revenue_deduction == True:
        #             if line.discount != 0 and not line.x_promotion_reason_id:
        #                 if not line.product_id.product_tmpl_id.categ_id.property_account_discount_vip_categ_id:
        #                     raise except_orm('Thông báo!', "Vui lòng cấu hình thêm tài khoản ghi sổ với hình thức VIP")
        #                 discount_total = (line.price_unit * line.qty - line.x_amount_promotion) * line.discount / 100
        #
        #                 inv_name = line.product_id.name
        #                 inv_line = {
        #                     'invoice_id': self.invoice_id.id,
        #                     'product_id': line.product_id.id,
        #                     'quantity': 1,
        #                     'discount': 0.0,
        #                     'price_unit': discount_total,
        #                     'account_id': line.product_id.product_tmpl_id.categ_id.property_account_discount_vip_categ_id.id,
        #                     'name': inv_name,
        #                 }
        #                 invoice_line = InvoiceLine.sudo().new(inv_line)
        #                 inv_line = invoice_line._convert_to_write(
        #                     {name: invoice_line[name] for name in invoice_line._cache})
        #                 inv_line.update(price_unit=discount_total, discount=0.0, name=inv_name)
        #                 InvoiceLine.create(inv_line)
        #             # Tạo thêm trong invoice line nếu có triết khấu là CTKM trên từng dong
        #             if line.x_amount_promotion != 0:
        #                 if not line.product_id.product_tmpl_id.categ_id.property_account_discount_tm_categ_id:
        #                     raise except_orm('Thông báo!', "Vui lòng cấu hình thêm tài khoản ghi sổ với hình thức CTKM")
        #                 discount_total = line.x_amount_promotion
        #
        #                 inv_name = line.product_id.name
        #                 inv_line = {
        #                     'invoice_id': self.invoice_id.id,
        #                     'product_id': line.product_id.id,
        #                     'quantity': 1,
        #                     'discount': 0.0,
        #                     'price_unit': discount_total,
        #                     'account_id': line.product_id.product_tmpl_id.categ_id.property_account_discount_tm_categ_id.id,
        #                     'name': inv_name,
        #                 }
        #                 invoice_line = InvoiceLine.new(inv_line)
        #                 inv_line = invoice_line._convert_to_write(
        #                     {name: invoice_line[name] for name in invoice_line._cache})
        #                 inv_line.update(price_unit=discount_total, discount=0.0, name=inv_name)
        #                 InvoiceLine.create(inv_line)
            # Thêm dòng invoice line nếu có CTKM trên toàn đơn hàng chia thành dịch vụ và đơn hàng
            # Chưa viết ... chờ CTKM tên toàn đơn hàng xong rồi làm tiếp
            # if self.x_amount_promotion_product != 0:
            #     x_amount_promotion_product_id = self.env['ir.config_parameter'].get_param(
            #         'point_of_sale.x_discount_product_id')
            #     x_amount_promotion_product = self.env['product.product'].search(
            #         [('id', '=', x_amount_promotion_product_id)])
            #     searchconfig_parameter = len(
            #         self.env['ir.config_parameter'].search([('key', '=', 'point_of_sale.x_discount_product_id')]))
            #     if searchconfig_parameter == 0:
            #         raise ValidationError(
            #             "Chưa có cầu hình thông số ghi nhận CTKM dịch vụ, cần liên hệ quản trị viên")
            #     inv_name = x_amount_promotion_product.name
            #     inv_line = {
            #         'invoice_id': self.invoice_id.id,
            #         'product_id': x_amount_promotion_product.id,
            #         'quantity': 1,
            #         'discount': 0.0,
            #         'price_unit': self.x_amount_promotion_product,
            #         'account_id': x_amount_promotion_product.product_tmpl_id.categ_id.property_account_income_categ_id.id,
            #         'name': inv_name,
            #     }
            #     invoice_line = InvoiceLine.new(inv_line)
            #     inv_line = invoice_line._convert_to_write(
            #         {name: invoice_line[name] for name in invoice_line._cache})
            #     inv_line.update(price_unit=self.x_amount_promotion_product, discount=0.0, name=inv_name)
            #     InvoiceLine.create(inv_line)
            # Nếu giảm giá toàn đơn hàng có dịch vụ
            # if self.x_amount_promotion_service != 0:
            #     x_amount_promotion_service_id = self.env['ir.config_parameter'].get_param(
            #         'point_of_sale.x_discount_service_id')
            #     x_amount_promotion_service = self.env['product.product'].search(
            #         [('id', '=', x_amount_promotion_service_id)])
            #     searchconfig_parameter = len(
            #         self.env['ir.config_parameter'].search([('key', '=', 'point_of_sale.x_discount_service_id')]))
            #     if searchconfig_parameter == 0:
            #         raise ValidationError(
            #             "Chưa có cầu hình thông số ghi nhận CTKM sản phẩm, cần liên hệ quản trị viên")
            #     inv_name = x_amount_promotion_service.name
            #     inv_line = {
            #         'invoice_id': self.invoice_id.id,
            #         'product_id': x_amount_promotion_service.id,
            #         'quantity': 1,
            #         'discount': 0.0,
            #         'price_unit': self.x_amount_promotion_service,
            #         'account_id': x_amount_promotion_service.product_tmpl_id.categ_id.property_account_income_categ_id.id,
            #         'name': inv_name,
            #     }
            #     invoice_line = InvoiceLine.new(inv_line)
            #     inv_line = invoice_line._convert_to_write(
            #         {name: invoice_line[name] for name in invoice_line._cache})
            #     inv_line.update(price_unit=self.x_amount_promotion_service, discount=0.0, name=inv_name)
            #     InvoiceLine.create(inv_line)
            # self.invoice_id.action_invoice_open()
            # self.account_move = self.invoice_id.move_id
            # payment = []
            # if self.invoice_id:
            #     for line in self.statement_ids:
            #         line.x_ignore_reconcile = True
            #         payment_methods = line.journal_id.inbound_payment_method_ids
            #         payment_method_id = payment_methods and payment_methods[0] or False
            #         # journal_debit_id = self.config_id.x_journal_debit_ids.ids if self.config_id.x_journal_debit_ids else False
            #         # Nếu có hình thức là ghi nợ thì bỏ qua thì ko tạo account.payment
            #         # if journal_debit_id:
            #         #     if line.journal_id.id in journal_debit_id:
            #         #         continue
            #         # Tạo account.payment gắn với hóa đơn đã tạo ra trong đơn refund
            #         if line.amount < 0:
            #             argvas = {
            #                 'amount': abs(line.amount),
            #                 'journal_id': line.journal_id.id,
            #                 'payment_date': line.date,
            #                 'communication': line.name,
            #                 'payment_method_id': payment_method_id.id,
            #                 'payment_type': 'outbound',
            #                 'invoice_ids': [(6, 0, self.invoice_id.ids)],
            #                 'partner_type': 'customer',
            #                 'partner_id': self.partner_id.id,
            #                 'x_intermediary_partner_id': line.x_intermediary_partner_id.id if line.x_intermediary_partner_id.id else False,
            #                 # added by HoiHD
            #             }
            #             account_payment = self.env['account.payment'].create(argvas)
            #             # if debt_total != 0:
            #             account_payment.action_validate_invoice_payment()
            #             # else:
            #             #     account_payment.post()
            #             #     payment.append(account_payment)
            #         # Tạo thanh toán thêm đối với số tiền khách hàng phải bù thêm
            #         else:
            #             argvs = {
            #                 'amount': line.amount,
            #                 'journal_id': line.journal_id.id,
            #                 'payment_date': line.date,
            #                 'communication': line.name,
            #                 'payment_type': 'inbound',
            #                 'payment_method_id': payment_method_id.id,
            #                 'partner_type': 'customer',
            #                 'partner_id': line.partner_id.id,
            #                 'x_intermediary_partner_id': line.x_intermediary_partner_id.id if line.x_intermediary_partner_id.id else False,
            #                 # added by HoiHD
            #             }
            #             pay = self.env['account.payment'].create(argvs)
            #             pay.post()
            #             payment.append(pay)
            # # Reconcile các bút toán với nhau
            # # + TH1 nếu đơn ban đầu thanh toán hết thì lúc refund không bỏ reconcile ban đầu mà tạo reconcile các bút toán sau khi refund
            # # + TH2 nếu đơn ban đầu lức có nợ thì bỏ reconcile đơn ban đầu sau đó reconcile lại toàn bộ cả đơn ban đầu và đơn refund
            # if self.invoice_id:
            #     if debt_total != 0:
            #         for inv in self.x_pos_partner_refund_id.invoice_id:
            #             movelines = inv.move_id.line_ids
            #             to_reconcile_ids = {}
            #             to_reconcile_lines = self.env['account.move.line']
            #             for line in movelines:
            #                 if line.account_id.id == inv.account_id.id:
            #                     to_reconcile_lines += line
            #                     to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
            #                 if line.reconciled:
            #                     line.remove_move_reconcile()
            #             for tmpline in self.invoice_id.move_id.line_ids:
            #                 if tmpline.account_id.id == inv.account_id.id:
            #                     to_reconcile_lines += tmpline
            #                     # tmpline.remove_move_reconcile()
            #             for x in payment:
            #                 for y in x.move_line_ids:
            #                     if y.account_id.id == inv.account_id.id:
            #                         to_reconcile_lines += y
            #             to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()


    def action_process_card_service(self):
        # # Cập nhật lại thẻ
        # + Nếu là trong cùng 1 phiên thì cập nhật lại trạng thái thẻ như trước khi bán và nhập lại kho để nhân viên bán lại
        # + Nếu khác phiên thì hủy thẻ và không nhâp lại kho
        journal_id = self.env['account.journal'].search([('id', '=', 11)], limit=1)
        for line in self.lines:
            # Nếu là phiếu mua hàng
            if line.product_id.product_tmpl_id.x_card_type == 'voucher':
                if line.qty <= 0:
                    if self.session_id.id == self.x_pos_partner_refund_id.session_id.id:
                        line.x_lot_id.x_state = 'activated'
                        line.x_lot_id.x_customer_id = False
                        line.x_lot_id.x_order_id = False
                        if line.x_lot_id.x_release_id.expired_type == 'flexible':
                            line.x_lot_id.life_date = ''
                    else:

                        line.x_lot_id.x_state = 'destroy'
                else:
                    line.x_lot_id.x_customer_id = self.partner_id.id
                    line.x_lot_id.x_state = 'using'
                    line.x_lot_id.x_order_id = self.id
                    if line.x_lot_id.x_release_id.expired_type == 'flexible':
                        raise except_orm('Thông báo', (
                            'Phiếu mua hàng không sử dụng phương thức hết hạn là linh hoạt. Vui lòng liện hệ quản trị viên để xử lý.'))
            if line.product_id.product_tmpl_id.x_card_type in ('service_card', 'keep_card'):
                if self.session_id.id == self.x_pos_partner_refund_id.session_id.id:
                    line.x_lot_id.x_state = 'activated'
                    line.x_lot_id.x_customer_id = False
                    line.x_lot_id.x_order_id = False
                    line.x_lot_id.x_used_count = 0
                    if line.x_lot_id.x_release_id.expired_type == 'flexible':
                        line.x_lot_id.life_date = ''
                    for x in line.x_lot_id.x_stock_production_lot_line_ids:
                        x.unlink()
                    use_service = self.env['pos.use.service.line'].search([('lot_id', '=', line.x_lot_id.id)])
                    for y in use_service:
                        y.lot_id = False
                else:
                    line.x_lot_id.x_state = 'destroy'
                # Nếu là thẻ dịch vụ
                if line.product_id.product_tmpl_id.x_card_type == 'service_card':
                    line.x_lot_id.x_total_count = 0
            for tmp in line.x_bundle_item_ids:
                if tmp.product_id.x_card_type == 'voucher':
                    if tmp.qty <= 0:
                        for x in tmp.product_item_lot_ids:
                            if self.session_id.id == self.x_pos_partner_refund_id.session_id.id:
                                x.lot_id.x_state = 'activated'
                                x.lot_id.x_customer_id = False
                                x.lot_id.x_order_id = False
                                if x.lot_id.x_release_id.expired_type == 'flexible':
                                    x.lot_id.life_date = ''
                            else:
                                x.lot_id.x_state = 'destroy'
                    else:
                        for x in tmp.product_item_lot_ids:
                            x.lot_id.x_customer_id = self.partner_id.id
                            x.lot_id.x_state = 'using'
                            x.lot_id.x_order_id = self.id
                            if x.lot_id.x_release_id.expired_type == 'flexible':
                                raise except_orm('Thông báo', (
                                    'Phiếu mua hàng không sử dụng phương thức hết hạn là linh hoạt. Vui lòng liện hệ quản trị viên để xử lý.'))
        # Xử lý các thẻ đã dùng để thanh toán sau đó refund đi
        # + Nếu cùng phiên thì trả lại cho khách hàng
        # + Nếu khác phien thì hủy cái thẻ đó di
        for x in self.statement_ids:
            if x.x_lot_ids:
                if self.session_id.id == self.x_pos_partner_refund_id.session_id.id:
                    for y in x.x_lot_ids:
                        y.x_state = 'using'
                        y.x_use_customer_id = False
                        y.x_used_count = 0
                else:
                    for y in x.x_lot_ids:
                        y.x_state = 'destroy'

    # Trừ điểm đổ
    # def action_red_point_refund(self):
    #     CustomerRedPointObj = self.env['pos.customer.red.point']
    #     CustomerRedPointHistoryObj = self.env['pos.customer.red.point.history']
    #     # Hoàn lại điểm đỏ của khách hàng nếu như đơn hàng ban đầu được cộng điểm đỏ.
    #     customer_red_point_historys = CustomerRedPointHistoryObj.search(
    #         [('order_id', '=', self.x_pos_partner_refund_id.id), ('partner_id', '=', self.partner_id.id)])
    #
    #     if self.x_use_red_point < 0 or self.x_red_point < 0:
    #         for history in customer_red_point_historys:
    #             if self.x_red_point < 0:
    #                 history.red_point_id.point -= history.point
    #             if self.x_use_red_point < 0:
    #                 history.red_point_id.used_point += history.point
    #             CustomerRedPointHistoryObj.create({
    #                 'used_date': self.date_order,
    #                 'order_id': self.id,
    #                 'point': - history.point,
    #                 'partner_id': self.partner_id.id,
    #                 'red_point_id': history.red_point_id.id,
    #             })
    #
    #     return True

    # Cập nhật lại voucher trong đơn hàng có bán bundle
    # Nếu trong bundle có thẻ voucher thì cập nhật lại trong voucher
    # + Nếu trong cùng phiên thì trả phiếu mua hàng và thực hiện nhập kho
    # + Nếu khác phiên thì hủy thẻ và không nhập lại kho
    def action_bundle_refund(self):
        if self.lines:
            for line in self.lines:
                if line.x_bundle_item_ids and line.product_id.type == 'bundle':
                    for bundle_item in line.x_bundle_item_ids:
                        if bundle_item.product_item_lot_ids and bundle_item.product_id.x_card_type == 'voucher':
                            for product_item_lot in bundle_item.product_item_lot_ids:
                                if bundle_item != 0:
                                    product_item_lot.lot_id.x_customer_id = False
                                    product_item_lot.lot_id.x_state = 'using'
                                    product_item_lot.lot_id.x_order_id = False
                                    if product_item_lot.lot_id.x_release_id.expired_type == 'flexible':
                                        product_item_lot.lot_id.life_date = ''
                                else:
                                    product_item_lot.lot_id.x_state = 'destroy'

    # def _check_count_card_refund(self):
    #     x_charge_refund_id = self.env['ir.config_parameter'].get_param('point_of_sale.x_charge_refund_id')
    #     x_charge_refund = self.env['product.product'].search(
    #         [('id', '=', x_charge_refund_id)])
    #     count_keep_card = 0
    #     count_service_card = 0
    #     count_service = 0
    #     for tmp in self.lines:
    #         if tmp.product_id.x_card_type == 'keep_card':
    #             count_keep_card = count_keep_card + 1
    #             # if tmp.qty != -1:
    #             #     raise except_orm('Thông báo',
    #             #                      'Bạn không thể bán nhiều thẻ dịch vụ hoặc không có số lượng trên một đơn hàng!')
    #         if tmp.product_id.x_card_type == 'service_card':
    #             count_service_card = count_service_card + 1
    #             # if tmp.qty != -1:
    #             #     raise except_orm('Thông báo',
    #             #                      'Bạn không thể bán nhiều thẻ dịch vụ hoặc không có số lượng trên một đơn hàng!')
    #         if (tmp.product_id.type == 'service' and tmp.product_id.x_card_type == 'none' and self.x_type != 'service' and tmp.product_id.id != x_charge_refund.id):
    #             count_service = count_service + 1
    #     if (count_keep_card + count_service_card) > 1:
    #         raise except_orm('Thông báo', 'Bạn không thể bán nhiều thẻ dịch vụ trên cùng một đơn hàng!')
    #     else:
    #         if count_keep_card == 1 and count_service == 0:
    #             raise except_orm('Thông báo', 'Vui lòng thêm một dịch vụ cho thẻ keep vừa chọn!')
    #         if count_keep_card == 1 and count_service > 2:
    #             raise except_orm('Thông báo', 'Thẻ keep chỉ bao gồm duy nhất một loại dịch vụ!')
    #         if count_service_card == 1 and count_service == 0:
    #             raise except_orm('Thông báo', 'Vui lòng thêm dịch vụ cho thẻ dịch vụ vừa chọn!')
    #         if (count_keep_card + count_service_card) == 0 and count_service != 0:
    #             raise except_orm('Thông báo', 'Bạn phải gắn thẻ dịch vụ cho các dịch vụ vừa chọn!')
    #     return True

    def _search_voucher(self, voucher):
        voucher_obj = self.env['stock.production.lot'].search([('name', '=', voucher)])
        if voucher_obj:
            if voucher_obj.x_state == 'destroy':
                self.env.cr.execute(
                    'SELECT account_bank_statement_line_id FROM account_bank_statement_line_stock_production_lot_rel WHERE stock_production_lot_id = %s ORDER BY account_bank_statement_line_id desc',
                    (str(voucher_obj.id),))
                # query = """SELECT account_bank_statement_line_id FROM account_bank_statement_line_stock_production_lot_rel WHERE stock_production_lot_id = %s"""
                # self._cr.execute(query, (voucher_obj.id,))
                vc = self.env.cr.fetchall()
                # self._cr.execute("""
                #                 select id from stock_production_lot where id = %s
                #             """, (voucher_obj.id,))
                # vc = self._cr.fetchall()
                if vc:
                    bank_statement_line = self.env['account.bank.statement.line'].search([('id', '=', vc[0])])
                    if bank_statement_line:
                        order_id = bank_statement_line.pos_statement_id
                        for line in order_id.lines:
                            if line.product_id.product_tmpl_id.x_card_type == 'voucher':
                                voucher_obj = self._search_voucher(line.x_lot_id.name)
        return voucher_obj

    @api.multi
    def action_refund_revenue_allaction(self):
        if abs(self.amount_total) == abs(self.x_pos_partner_refund_id.amount_total):
            PosRevenueAllocation = self.env['pos.revenue.allocation']
            PosRevenueAllocationLine = self.env['pos.revenue.allocation.line']
            for line in self.x_pos_partner_refund_id.revenue_allocation_ids:
                argvs = {
                    'name': line.name,
                    'order_id': self.id,
                    'amount_total': -line.amount_total,
                    'remain_amount': -line.remain_amount,
                    'style_allocation': line.style_allocation,
                    'state': line.state,
                    'amount_product': -line.amount_product,
                    'amount_service': -line.amount_service,
                    'amount_keep': -line.amount_keep,
                }
                pos_revenue_allocation_id = PosRevenueAllocation.create(argvs)
                for x in line.revenue_allocation_ids:
                    argvs_line = {
                        'employee_id': x.employee_id.id,
                        'amount_product': -x.amount_product,
                        'amount_service': -x.amount_service,
                        'amount_keep': -x.amount_keep,
                        'amount_product_percent': x.amount_product_percent,
                        'amount_service_percent': x.amount_service_percent,
                        'amount_keep_percent': x.amount_keep_percent,
                        'revenue_allocation_id': pos_revenue_allocation_id.id,
                    }
                    PosRevenueAllocationLine.create(argvs_line)
