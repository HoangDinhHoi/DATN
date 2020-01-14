# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from odoo.tools import float_is_zero
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _default_team(self):
        pos_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        return pos_session.config_id.crm_team_id.id

    x_revenue = fields.Float("Revenue")
    x_team_id = fields.Many2one('crm.team', "Team", default=_default_team)
    x_type = fields.Selection([('pos', "Pos"), ('service', "Service")], default='pos')
    state = fields.Selection(selection_add=[('confirm', 'Confirm'), ('wait_confirm', 'Wait Confirm')])

    amount_paid = fields.Float(string='Paid', states={'draft': [('readonly', False)]},
                               readonly=True, digits=0, default=0)
    amount_return = fields.Float(string='Returned', digits=0, readonly=True, default=0)
    x_pos_partner_refund_id = fields.Many2one('pos.order', "POS Order Refund")
    picking_id = fields.Many2many('stock.picking', string='Picking', readonly=True, copy=False)

    @api.onchange('lines', 'partner_id')
    def onchange_amount(self):
        self.amount_paid = 0
        self.amount_return = 0

    @api.constrains('lines')
    def _check_lines(self):
        for s in self.filtered(lambda s: s.lines):
            for line in s.lines.filtered(lambda l: l.product_id.type in ['product']):
                if line.qty <= 0 and not line.order_id.x_pos_partner_refund_id: raise ValidationError(
                    "Số lượng bán sản phẩm %s phải lớn hơn 0!" % (line.product_id.name,))
                context = {
                    'location': s.location_id.id,
                }
                res = line.product_id.with_context(context)._product_available()
                if res[line.product_id.id]['qty_available'] < abs(line.qty):
                    raise ValidationError(
                        "Sản phẩm %s không đủ hàng (%s) trong kho %s" % (line.product_id.name, res[line.product_id.id]['qty_available'], s.location_id.name))

    @api.onchange('lines')
    #     Sang La thêm 26/04/2019 tính x_revenue_rate của sản phẩm dịch vụ vào trong pos_order_line
    # Cập nhật lại trường x_revenue_rate trên từng order_line
    def _action_update_revenue_rate_order_line(self):
        total_revenue = 0
        total = 0
        count = len(self.lines)
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

    @api.model
    def default_get(self, fields):
        res = super(PosOrder, self).default_get(fields)
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        if not current_session:
            raise except_orm(("Thông báo"), ('You open session before create order.'))
        return res

    @api.multi
    def action_pos_order_paid(self):
        # if self.x_type == 'service':
        #     raise except_orm('Thông báo', "Đây là đơn sử dụng dịch vụ. Bạn cần vào sử dụng dịch vụ để thông toán")
        if not self.test_paid():
            raise UserError("Order is not paid.")
        super(PosOrder, self.with_context(create_picking=True)).action_pos_order_paid()
        self.write({'state': 'draft'})


    def create_picking(self):
        # đặt context để khi thanh toán xong chưa xuát kho mà ấn nút xác nhận mới xuất kho
        if self._context.get('create_picking', False):
            return True
        # Viết lại hàm create_piking của core để thêm sản phầm trong bundle vào picking
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu', 'bundle']):
                continue
            address = order.partner_id.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = order.location_id.id
            if (not picking_type) or (not picking_type.default_location_dest_id):
                raise except_orm('Thông báo', ('Bạn chưa cấu hình loại dịch chuyển trên điểm bán hàng này hoặc đã cấu hình thiếu. Vui lòng kiểm tra lại!'))
            destination_id = picking_type.default_location_dest_id.id
            if picking_type:
                message = _(
                    "This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                              order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                    'branch_id': order.branch_id.id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu', 'bundle']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    order_picking.message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu', 'bundle']])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    return_picking.message_post(body=message)

            for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty,precision_rounding=l.product_id.uom_id.rounding)):
                moves |= Move.create({
                    'name': line.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                    'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': abs(line.qty),
                    'state': 'draft',
                    'branch_id': order.branch_id.id,
                    'location_id': location_id if line.qty >= 0 else destination_id,
                    'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                })

            # prefer associating the regular order picking, not the return
            picking_ids = []
            if order_picking:
                picking_ids.append(order_picking.id)
            if return_picking:
                picking_ids.append(return_picking.id)
            order.write({'picking_id': [(4, x) for x in picking_ids]})
            # order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # gói cập nhật sau
            for line in order.lines.filtered(lambda l: l.product_id.type in ['bundle'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                for bundle_item in line.x_bundle_item_ids:
                    if bundle_item.product_id.type == 'service':
                        continue

                    move_id = Move.create({
                        'name': line.name,
                        'product_uom': bundle_item.product_id.uom_id.id,
                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        'picking_type_id': picking_type.id if bundle_item.qty >= 0 else return_pick_type.id,
                        'product_id': bundle_item.product_id.id,
                        'state': 'done',
                        'branch_id': order.branch_id.id,
                        'location_id': location_id if bundle_item.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if bundle_item.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                    })
                    if bundle_item.product_item_lot_ids:
                        for product_item_lot in bundle_item.product_item_lot_ids:
                            # if product_item_lot.lot_ids:
                            #     for lot in product_item_lot.lot_ids:
                            self.env['stock.move.line'].create({'product_id': bundle_item.product_id.id,
                                'lot_id': product_item_lot.lot_id.id,
                                'product_uom_id': bundle_item.uom_id.id,
                                # 'product_uom_qty': abs(product_item_lot.qty),
                                'qty_done': abs(product_item_lot.qty),
                                'package_id': False,
                                'result_package_id': False,
                                'owner_id': False,
                                'state': 'done',
                                'location_id': location_id if bundle_item.qty >= 0 else destination_id,
                                'location_dest_id': destination_id if bundle_item.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                                'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                                'move_id': move_id.id, })
                    else:
                        self.env['stock.move.line'].create({'product_id': bundle_item.product_id.id,
                            'product_uom_id': bundle_item.uom_id.id,
                            # 'product_uom_qty': abs(product_item_lot.qty),
                            'qty_done': abs(bundle_item.qty),
                            'package_id': False,
                            'result_package_id': False,
                            'owner_id': False,
                            'state': 'done',
                            'location_id': location_id if bundle_item.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if bundle_item.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                            'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                            'move_id': move_id.id, })

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()
        return True

    def _force_picking_done(self, picking):
        """Force picking in order to be set as done."""
        self.ensure_one()
        # tiennq edit
        if len(picking.move_lines) == 0:
            return picking.state == 'done'
        picking.action_assign()
        wrong_lots = self.set_pack_operation_lot(picking)
        if not wrong_lots:
            picking.action_done()

    @api.multi
    def action_confirm_order(self):
        # if self.state != 'draft':
        #     raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui long F5 hoặc load lại trang"))
        # self.state = 'invoiced'
        if len(self.lines) == 0:
            raise except_orm('Thông báo!', ("Bạn cần có sản phẩm hoặc dịch vụ trước khi xác nhận"))
        amount_payment = 0
        for line in self.statement_ids:
            amount_payment += line.amount
        if amount_payment != round(self.amount_total,2):
            raise except_orm('Thông báo!', ("Bạn cần thanh toán đủ trước khi xác nhận đơn hàng"))
        if self.amount_total != 0:
            self.action_pos_order_invoice()
            self.invoice_id.update({'team_id': self.x_team_id.id})
            # for line in self.lines:
            #     InvoiceLine = self.env['account.invoice.line']
            #     # Tạo thêm invoice line nếu có triết kkhaau VIP trên đó
            #     if line.product_id.product_tmpl_id.categ_id.revenue_deduction == True:
            #         if line.discount != 0 and not line.x_promotion_reason_id:
            #             if not line.product_id.product_tmpl_id.categ_id.property_account_discount_vip_categ_id:
            #                 raise except_orm('Thông báo!', "Vui lòng cấu hình thêm tài khoản ghi sổ với hình thức VIP")
            #             discount_total = (line.price_unit*line.qty - line.x_amount_promotion)*line.discount/100
            #
            #             inv_name = line.product_id.name
            #             inv_line = {
            #                 'invoice_id': self.invoice_id.id,
            #                 'product_id': line.product_id.id,
            #                 'quantity': 1,
            #                 'discount': 0.0,
            #                 'price_unit': -discount_total,
            #                 'account_id': line.product_id.product_tmpl_id.categ_id.property_account_discount_vip_categ_id.id,
            #                 'name': inv_name,
            #             }
            #             invoice_line = InvoiceLine.new(inv_line)
            #             inv_line = invoice_line._convert_to_write(
            #                 {name: invoice_line[name] for name in invoice_line._cache})
            #             inv_line.update(price_unit=-discount_total, discount=0.0, name=inv_name)
            #             InvoiceLine.create(inv_line)
            #         # Tạo thêm trong invoice line nếu có triết khấu là CTKM trên từng dong
            #         if line.x_amount_promotion != 0:
            #             if not line.product_id.product_tmpl_id.categ_id.property_account_discount_tm_categ_id:
            #                 raise except_orm('Thông báo!', "Vui lòng cấu hình thêm tài khoản ghi sổ với hình thức CTKM")
            #             discount_total = line.x_amount_promotion
            #
            #             inv_name = line.product_id.name
            #             inv_line = {
            #                 'invoice_id': self.invoice_id.id,
            #                 'product_id': line.product_id.id,
            #                 'quantity': 1,
            #                 'discount': 0.0,
            #                 'price_unit': -discount_total,
            #                 'account_id': line.product_id.product_tmpl_id.categ_id.property_account_discount_tm_categ_id.id,
            #                 'name': inv_name,
            #             }
            #             invoice_line = InvoiceLine.new(inv_line)
            #             inv_line = invoice_line._convert_to_write(
            #                 {name: invoice_line[name] for name in invoice_line._cache})
            #             inv_line.update(price_unit=-discount_total, discount=0.0, name=inv_name)
            #             InvoiceLine.create(inv_line)
            # Thêm dòng invoice line nếu có CTKM trên toàn đơn hàng chia thành dịch vụ và đơn hàng
            # Chưa viết ... chờ CTKM tên toàn đơn hàng xong rồi làm tiếp
            # Nếu giảm giá toàn đơn hàng có đơn hàng
            # if self.x_amount_promotion_product != 0:
            #     x_amount_promotion_product_id = self.env['ir.config_parameter'].get_param('point_of_sale.x_discount_product_id')
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
            #         'price_unit': -self.x_amount_promotion_product,
            #         'account_id': x_amount_promotion_product.product_tmpl_id.categ_id.property_account_income_categ_id.id,
            #         'name': inv_name,
            #     }
            #     invoice_line = InvoiceLine.new(inv_line)
            #     inv_line = invoice_line._convert_to_write(
            #         {name: invoice_line[name] for name in invoice_line._cache})
            #     inv_line.update(price_unit=-self.x_amount_promotion_product, discount=0.0, name=inv_name)
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
            #         'price_unit': -self.x_amount_promotion_service,
            #         'account_id': x_amount_promotion_service.product_tmpl_id.categ_id.property_account_income_categ_id.id,
            #         'name': inv_name,
            #     }
            #     invoice_line = InvoiceLine.new(inv_line)
            #     inv_line = invoice_line._convert_to_write(
            #         {name: invoice_line[name] for name in invoice_line._cache})
            #     inv_line.update(price_unit=-self.x_amount_promotion_service, discount=0.0, name=inv_name)
            #     InvoiceLine.create(inv_line)
            # Xác nhận hóa đơn
            self.invoice_id.sudo().action_invoice_open()
            self.account_move = self.invoice_id.move_id

            # Tạo thanh toán và reconsile đơn hàng luông
            payment_obj = self.env['account.payment']
            # x_journal_debit_ids = self.config_id.x_journal_debit_ids.ids if self.config_id.x_journal_debit_ids else False
            total = 0.0  # Tổng đơn hàng
            residual = 0.0  # Số còn nợ
            paid_statements = []
            for statement in self.statement_ids:
                total += statement.amount
                # if x_journal_debit_ids and (statement.journal_id.id in x_journal_debit_ids):
                #     residual += statement.amount
                # else:
                #     paid_statements.append(statement)
            for statement in paid_statements:
                payment_methods = statement.journal_id.inbound_payment_method_ids
                payment_method_id = payment_methods and payment_methods[0] or False
                pay = payment_obj.create({
                    'amount': statement.amount,
                    'journal_id': statement.journal_id.id,
                    'payment_date': statement.date,
                    'communication': statement.name,
                    'payment_type': 'inbound',
                    'payment_method_id': payment_method_id.id,
                    'invoice_ids': [(6, 0, self.invoice_id.ids)],
                    'partner_type': 'customer',
                    'partner_id': statement.partner_id.id,
                    'branch_id': self.branch_id.id # them boi HoiHD: them chi nhanh
                })
                pay.action_validate_invoice_payment()
            # self.statement_ids.write({'x_ignore_reconcile': True})
        x_journal_loyal_ids = self.config_id.x_journal_loyal_ids.ids if self.config_id.x_journal_loyal_ids else False
        if x_journal_loyal_ids:
            loyal_total = 0.0
            for stt in self.statement_ids:
                if stt.journal_id.id in x_journal_loyal_ids:
                    if stt.amount > 0:
                        loyal_total += stt.amount
            # Ghi nhận doanh thu
            if loyal_total > 0:
                self.update({'x_revenue': loyal_total})
        self.create_picking()

    # Cập nhật lại trường discount trong invoice do đẩy riêng 1 dòng không dùng chung nữa
    # def _action_create_invoice_line(self, line=False, invoice_id=False):
    #     invoice_line = super(PosOrder, self)._action_create_invoice_line(line, invoice_id)
    #     if line.discount:
    #         if not line.x_promotion_reason_id:
    #             invoice_line.update({'discount': 0})
    #     if line.order_id.x_pos_partner_refund_id:
    #         if line.qty !=0:
    #             if line.product_id.product_tmpl_id.categ_id.revenue_deduction == False :
    #                 invoice_line.update({'price_unit': (line.price_unit * line.qty - line.x_amount_promotion) * (1 - line.discount / 100)/line.qty})
    #                 print((line.price_unit * line.qty - line.x_amount_promotion) * (1 - line.discount / 100))
    #     else:
    #         invoice_line.update({'price_unit': (line.price_unit * line.qty - line.x_amount_promotion) * (
    #                     1 - line.discount / 100) / line.qty})
    #     return invoice_line


    # Sangsla ghi đề hàm set lot của core
    #  Nếu refund ddonw hàng theo lot core đang đẩy vời qty_done của stock_move số lượng âm ==> Sai ko refund được
    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done."""

        StockProductionLot = self.env['stock.production.lot']
        PosPackOperationLot = self.env['pos.pack.operation.lot']
        has_wrong_lots = False
        for order in self:
            for move in (picking or self.picking_id).move_lines:
                picking_type = (picking or self.picking_id).picking_type_id
                lots_necessary = True
                if picking_type:
                    lots_necessary = picking_type and picking_type.use_existing_lots
                qty_done = 0
                pack_lots = []
                pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', move.product_id.id)])

                if pos_pack_lots and lots_necessary:
                    for pos_pack_lot in pos_pack_lots:
                        stock_production_lot = StockProductionLot.search([('name', '=', pos_pack_lot.lot_name), ('product_id', '=', move.product_id.id)])
                        if stock_production_lot:
                            # a serialnumber always has a quantity of 1 product, a lot number takes the full quantity of the order line
                            qty = 1.0
                            if stock_production_lot.product_id.tracking == 'lot':
                                qty = pos_pack_lot.pos_order_line_id.qty
                            qty_done += qty
                            pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
                        else:
                            has_wrong_lots = True
                elif move.product_id.tracking == 'none' or not lots_necessary:
                    qty_done = move.product_uom_qty
                else:
                    has_wrong_lots = True
                for pack_lot in pack_lots:
                    lot_id, qty = pack_lot['lot_id'], pack_lot['qty']
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'picking_id': (picking or self.picking_id).id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'qty_done': abs(qty),
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'lot_id': lot_id,
                    })
                if not pack_lots and not float_is_zero(qty_done, precision_rounding=move.product_uom.rounding):
                    if len(move._get_move_lines()) < 2:
                        move.quantity_done = qty_done
                    else:
                        move._set_quantity_done(qty_done)
        return has_wrong_lots
