# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_signature = fields.Binary('Signature Image', attachment=True)
    state = fields.Selection(selection_add=[('customer_confirm', 'Customer Confirm')])
    x_service_lot_line_ids = fields.One2many('pos.service.lot', 'order_id', string="Order Lot")
    x_service_lot_ids = fields.Many2many('stock.production.lot', string='Lot/Serial Number')

    # x_custmer_confirm_id = fields.Many2one('pos.customer.confirm', "Customer Confirm")

    @api.multi
    def action_customer_confirm_order(self):
        if len(self.lines) == 0:
            raise except_orm('Thông báo!', ("Bạn cần có sản phẩm hoặc dịch vụ trước khi xác nhận"))
        amount_payment = 0
        for line in self.statement_ids:
            amount_payment += line.amount
        if amount_payment != round(self.amount_total,2):
            raise except_orm('Thông báo!', ("Bạn cần thanh toán đủ trước khi xác nhận đơn hàng"))
        if self.x_type == 'service':
            return self.action_customer_confirm_order_popup()
        PosServiceLot = self.env['pos.service.lot']
        self.x_service_lot_ids = False
        for item in self.x_service_lot_line_ids:
            item.unlink()
        count_service = 0
        for line in self.lines:
            # check thêm số lượng thực xuất
            # if line.product_id.tracking != 'none' and not line.x_lot_id and line.qty_export != 0:
            #     raise except_orm('Thông báo.', ('Vui lòng nhập mã lot/serial cho sản phẩm "%s"' % line.product_id.name))
            if line.product_id.x_card_type in ('service_card', 'keep_card'):
                self.x_service_lot_ids = [(4, line.x_lot_id.id)]
            if line.product_id.type == 'service' and line.product_id.default_code not in ('DVKHACMENARD', 'SPKHACMENARD', 'SPBANTANGGIA', 'DVBANTANGGIA'):
                count_service += 1
                PosServiceLot.create({
                    'service_id': line.product_id.id,
                    'order_id': self.id,
                    'order_line_id': line.id,
                })
            if line.product_id.type == 'bundle':
                for item in line.x_bundle_item_ids:
                    if item.product_id.type == 'service':
                        count_service += 1
                        PosServiceLot.create({
                            'service_id': item.product_id.id,
                            'order_id': self.id,
                            'order_line_id': line.id,
                            'bundle_id': item.id
                        })

        if len(self.x_service_lot_ids.ids) == 0 and count_service > 0:
            raise except_orm("Thông báo!", ("Vui lòng thêm ít nhất một thẻ khi đơn bán có dịch vụ"))
        if len(self.x_service_lot_ids.ids) == 0 and count_service == 0:
            return self.action_customer_confirm_order_popup()
        if len(self.x_service_lot_ids.ids) >= 1 and count_service == 0:
            raise except_orm("Thông báo!", ("Vui lòng thêm ít nhất một dịch vụ khi đơn bán có thẻ dịch vụ"))
        if len(self.x_service_lot_ids.ids) == 1 and count_service > 0:
            for item in self.x_service_lot_line_ids:
                item.lot_id = self.x_service_lot_ids.ids[0]
            return self.action_customer_confirm_order_popup()
        if len(self.x_service_lot_ids.ids) > 1:
            if count_service < len(self.x_service_lot_ids.ids):
                raise except_orm("Thông báo!", ("Số lượng thẻ nhiều hơn số lượng dịch vụ. Vui lòng kiểm tra lại"))
            view = self.env.ref('izi_pos_customer_confirm.pos_service_lot_form_view')
            return {
                'name': _('Lot Selection'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }


    @api.multi
    def action_customer_confirm_order_popup(self):
        for item in self.x_service_lot_line_ids:
            if not item.lot_id:
                raise except_orm("Thông báo!", ("Vui lòng thêm thẻ cho từng dịch vụ"))
        if self.session_id.config_id.module_izi_pos_customer_confirm == True:
            self.update({'state': 'customer_confirm'})
        else:
            if self.state != 'draft':
                raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
            self.state = 'invoiced'
            return self.action_confirm_order() # add by HoiHd

    @api.multi
    def action_customer_confirm(self):
        view = self.env.ref('izi_pos_customer_confirm.izi_pos_order_confirm_form')
        return {
            'name': _('Sign Customer?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def action_customer_signature(self):
        if self.state != 'customer_confirm':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'invoiced'
        return self.action_confirm_order()  # add by HoiHD
        # return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_back(self):
        if self.state != 'customer_confirm':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.x_signature = ''
        self.state = 'draft'

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
    # Tạo bút toán trích trước giá vốn khi bán thẻ
    def _create_credit_move_line(self, pos_oder_line, debit_account, credit_account, name_voucher):
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

    # Tạo trích trước giá vốn khi bán sản phẩm < 14% >
    def _create_record_entry_cost_deduction(self):
        account_113 = 1134
        # Bán
        if not self.x_pos_partner_refund_id:
            for line in self.lines:
                if line.product_id.x_card_type == 'voucher':
                    if line.product_id.accrued_capital_cost:
                        debit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_debt_id.id)
                        credit_account = self._check_account_exist(line.product_id.account_accrued_default_cost_id.id)
                        self._create_credit_move_line(line, debit_account, credit_account, line.x_lot_id.name)

            for line in self.statement_ids:
                if line.journal_id.type == 'coupon':
                    #Lấy ra voucher
                    query = '''SELECT * FROM account_bank_statement_line_stock_production_lot_rel WHERE account_bank_statement_line_id = %s limit 1'''
                    self._cr.execute(query, (line.id,))
                    production_statement_line_ojb = self._cr.dictfetchone()
                    voucher_ojb = self.env['stock.production.lot'].search(
                        [('id', '=', production_statement_line_ojb['stock_production_lot_id'])], limit=1)

                    debit_account_ojb = self.env['account.account'].search(
                        [('code', '=', '1134'),
                         ('company_id', '=', self.company_id.id)], limit=1)
                    if not debit_account_ojb:
                        raise except_orm('Thông báo', (
                                'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))
                    if voucher_ojb.product_id.accrued_capital_cost:
                        debit_account = debit_account_ojb.id
                        credit_account = self.env['account.account'].search(
                            [('code', '=', self.check_account_for_coupon_standard_price()),
                             ('company_id', '=', self.company_id.id)], limit=1)
                        if not credit_account:
                            raise except_orm('Thông báo', (
                                    'Tài khoản "%s" chưa cấu hình' % self.check_account_for_coupon_standard_price()))

                        self._create_credit_move_line(voucher_ojb, debit_account, credit_account.id,
                                                      voucher_ojb.name)
        # Refund
        else:
            pass


    @api.multi
    def action_confirm_order(self):
        # self._check_count_card()
        self._action_update_revenue_rate_order_line_multi()
        # cap nhat thong tin the, pmh
        loyal_total = 0.0
        x_journal_loyal_ids = self.config_id.x_journal_loyal_ids.ids if self.config_id.x_journal_loyal_ids else False
        if x_journal_loyal_ids:
            for stt in self.statement_ids:
                if stt.journal_id.id in x_journal_loyal_ids:
                    if stt.amount > 0:
                        loyal_total += stt.amount
        for line in self.lines:
            if line.x_lot_id and line.product_id.x_card_type == 'voucher':
                line.x_lot_id.x_customer_id = self.partner_id.id
                line.x_lot_id.x_state = 'using'
                line.x_lot_id.x_order_id = self.id
                if line.x_lot_id.x_release_id.expired_type == 'flexible':
                    raise except_orm('Thông báo', ('Phiếu mua hàng không sử dụng phương thức hết hạn là linh hoạt. Vui lòng liện hệ quản trị viên để xử lý.'))
        StockProductionLot = self.env['stock.production.lot.line']
        for item in self.x_service_lot_line_ids:
            argvs = {
                'product_id': item.service_id.id,
                'total_count': item.order_line_id.qty if not item.bundle_id else item.bundle_id.qty,
                'used_count': 0,
                'stock_production_lot_id': item.lot_id.id,
                'price_unit': item.order_line_id.price_unit if not item.bundle_id else self.pricelist_id.get_product_price(item.bundle_id.product_id,
                                                                                                                           item.bundle_id.qty,
                                                                                                                           self.partner_id),
                'price_sub_total': item.order_line_id.x_revenue_rate * loyal_total if not item.bundle_id else item.order_line_id.x_revenue_rate * loyal_total * item.bundle_id.revenue_rate / 100,
                'remain_sub_total': item.order_line_id.x_revenue_rate * loyal_total if not item.bundle_id else item.order_line_id.x_revenue_rate * loyal_total * item.bundle_id.revenue_rate / 100,
            }
            if all([x.product_id.id != item.service_id.id for x in item.lot_id.x_stock_production_lot_line_ids]) or len(item.lot_id.x_stock_production_lot_line_ids) == 0:
                StockProductionLot.create(argvs)
            else:
                for detail in item.lot_id.x_stock_production_lot_line_ids:
                    if detail.product_id.id == item.service_id.id:
                        # # (chương trình khuyến mại mua m lần DV A tặng n lần DV A thì phải cập nhật lại số lượng của stock_production_lot)
                        # detail.stock_production_lot_id.x_total_count += item.order_line_id.qty if not item.bundle_id else item.bundle_id.qty
                        detail.total_count += item.order_line_id.qty if not item.bundle_id else item.bundle_id.qty
                        detail.price_sub_total += item.order_line_id.x_revenue_rate * loyal_total if not item.bundle_id else item.order_line_id.x_revenue_rate * loyal_total * item.bundle_id.revenue_rate / 100
                        detail.remain_sub_total += item.order_line_id.x_revenue_rate * loyal_total if not item.bundle_id else item.order_line_id.x_revenue_rate * loyal_total * item.bundle_id.revenue_rate / 100
            if item.lot_id.x_state == 'activated':
                item.lot_id.write({
                    'x_customer_id': self.partner_id.id,
                    'x_state': 'using',
                    'x_order_id': self.id
                })
                #
                # item.lot_id.x_customer_id = self.partner_id.id
                # item.lot_id.x_state = 'using'
                # item.lot_id.x_order_id = self.id
            if item.lot_id.product_id.x_card_type == 'service_card':
                item.lot_id.x_total_count += item.order_line_id.qty if not item.bundle_id else item.bundle_id.qty

            if item.lot_id.product_id.x_card_type == 'keep_card':
                count = 0
                for line in self.lines:
                    if line.product_id.type == 'service':
                        count += line.qty
                if item.lot_id.x_total_count < count:
                    raise except_orm('Thông báo', ('Tổng số lần sử dụng trong đơn hàng lớn hơn số lần tối đa của thẻ. Vui lòng kiểm tra lại!!!.'))

        #cap nhat lai han the khi da co so luong
        for item in self.x_service_lot_line_ids:
            if item.lot_id.x_release_id.expired_type == 'flexible':
                rule_card_id = self.env['pos.rule.card.expirate'].search(
                    [('start_date', '<=', self.date_order.utcnow().date()), ('end_date', '>=', self.date_order.utcnow().date()), ('active', '=', True)])
                if len(rule_card_id) == 0:
                    raise except_orm('Thông báo', ('Chưa cấu hình quy tắc hạn thẻ. Vui lòng liện hệ quản trị viên.'))
                if len(rule_card_id) > 1:
                    raise except_orm('Thông báo', ('Có lớn hơn 1 quy tắc hạn thẻ khả dụng. Vui lòng liện hệ quản trị viên.'))
                x_month = rule_card_id._compute_month(item.lot_id.product_id.x_card_type, item.lot_id.x_total_count)
                item.lot_id.life_date = self.date_order.utcnow().date() + relativedelta(months=x_month)
        # cap nhạt thong tin pmh thanh toan
        for line in self.statement_ids:
            for item in line.x_lot_ids:
                item.x_state = 'used'
                item.x_use_customer_id = self.partner_id.id
                item.x_used_count = 1
                item.x_order_use_id = self.id
        # cap nhat lot
        for line in self.lines:
            if line.x_lot_id:
                pos_pack_id = self.env['pos.pack.operation.lot'].search([('pos_order_line_id', '=', line.id), ('lot_name', '=', line.x_lot_id.name)], limit=1)
                if pos_pack_id.id == False:
                    argv = {
                        'pos_order_line_id': line.id,
                        'lot_name': line.x_lot_id.name,
                    }
                    self.env['pos.pack.operation.lot'].create(argv)
        # cập nhật lại thông tin thẻ nếu trong gói có thẻ voucher
        for line in self.lines:
            if line.product_id.type == 'bundle':
                for item in line.x_bundle_item_ids:
                    if item.product_id.x_card_type == 'voucher':
                        for lot in item.product_item_lot_ids:
                            lot.lot_id.x_customer_id = self.partner_id.id
                            lot.lot_id.x_state = 'using'
                            lot.lot_id.x_order_id = self.id
                            if lot.lot_id.x_release_id.expired_type == 'flexible':
                                raise except_orm('Thông báo', (
                                    'Phiếu mua hàng không sử dụng phương thức hết hạn là linh hoạt. Vui lòng liện hệ quản trị viên để xử lý.'))

        # trích trước khi bán ra
        self._create_record_entry_cost_deduction()

        return super(PosOrder, self).action_confirm_order()

class PosServiceLot(models.Model):
    _name = 'pos.service.lot'

    service_id = fields.Many2one('product.product', 'Service')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    order_id = fields.Many2one('pos.order', 'Order')
    order_line_id = fields.Many2one('pos.order.line', 'Order Line')
    bundle_id = fields.Many2one('pos.order.product.item', 'Bundle Line')

