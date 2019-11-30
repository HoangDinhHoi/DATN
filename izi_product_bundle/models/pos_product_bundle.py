# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_add_a_bundle(self):
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_order_id': self.id,
                    # 'default_x_location_id': self.location_id.id
                    })
        view = self.sudo().env.ref('izi_product_bundle.pos_order_line_bundle_form_view')
        return {
            'name': 'Order line',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_confirm_order(self):
        if self.lines:
            for line in self.lines:
                if line.x_bundle_item_ids and line.product_id.type == 'bundle':
                    for bundle_item in line.x_bundle_item_ids:
                        if bundle_item.product_item_lot_ids and bundle_item.product_id.x_card_type == 'voucher':
                            for product_item_lot in bundle_item.product_item_lot_ids:
                                product_item_lot.lot_id.x_customer_id = self.partner_id.id
                                product_item_lot.lot_id.x_state = 'using'
                                product_item_lot.lot_id.x_order_id = self.id
                                if product_item_lot.lot_id.x_release_id.expired_type == 'flexible':
                                    raise except_orm('Thông báo', (
                                        'Phiếu mua hàng không sử dụng phương thức hết hạn là linh hoạt. Vui lòng liện hệ quản trị viên để xử lý.'))
        return super(PosOrder, self).action_confirm_order()


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_bundle_item_ids = fields.One2many('pos.order.product.item', 'order_line_id', string="Bundle items")
    x_type_product = fields.Selection(related='product_id.type', string="Type product", readonly=1)

    @api.onchange('qty')
    def _onchange_izi_product_bundle_qty(self):  # them ten module do core đã sử dụng hàm _onchange_qty
        if self.x_bundle_item_ids:
            for bundle_item in self.x_bundle_item_ids:
                for bundle_option in bundle_item.bundle_component_id.bundle_option_ids:
                    if bundle_option.product_id == bundle_item.product_id:
                        bundle_item.qty = bundle_option.qty * self.qty
                        break

    @api.constrains('order_id')
    def _check_order_id(self):
        for s in self:
            s.order_id._onchange_amount_all()

    @api.constrains('x_bundle_item_ids')
    def _check_bundle_item_ids(self):
        for s in self:
            date_order = s.order_id.date_order.utcnow().date()
            list_lot_id = []
            check_quant_lot = []
            for bundle_item in s.x_bundle_item_ids:
                if not bundle_item.product_item_lot_ids and bundle_item.tracking_product in ['lot', 'serial'] and bundle_item.qty_export != 0: raise ValidationError(
                    "Sản phẩm được truy vết theo %s. Vui lòng chọn %s tương ứng." % (bundle_item.tracking_product, bundle_item.tracking_product,))
                if bundle_item.tracking_product == 'none':
                    if bundle_item.product_id.type == 'service':
                        continue
                    # Kiểm tra tồn hàng trong kho hàng bán
                    context = {'location': s.order_id.location_id.id, }
                    res = bundle_item.product_id.with_context(context)._product_available()
                    # nếu trong kho hàng bán không có thì kiểm tra tồn hàng trong kho ký gửi
                    if res[bundle_item.product_id.id]['qty_available'] < bundle_item.qty_export:
                        context = {'location': s.order_id.session_id.config_id.consign_location_id.id, }
                        res = bundle_item.product_id.with_context(context)._product_available()
                        if res[bundle_item.product_id.id]['qty_available'] < bundle_item.qty_export:
                            raise ValidationError("Sản phẩm %s không đủ hàng (%s) trong kho %s" % (
                                bundle_item.product_id.name, res[bundle_item.product_id.id]['qty_available'], s.order_id.location_id.name))
                elif bundle_item.tracking_product == 'lot':
                    count_qty_lot = 0
                    for product_item_lot in bundle_item.product_item_lot_ids:
                        if product_item_lot.lot_id.life_date and product_item_lot.lot_id.life_date + timedelta(days=1) <= date_order:
                            raise ValidationError("Mã lot/serial: %s bạn nhập trong sản phẩm %s đã hết hạn" % (
                                product_item_lot.lot_id.name, bundle_item.product_id.name))
                        # context = {
                        #     'lot_id': product_item_lot.lot_id.id,
                        #     'location': s.order_id.location_id.id,
                        # }
                        # qty = product_item_lot.qty
                        #
                        # if product_item_lot.lot_id.id in list_lot_id:
                        #     for cql in check_quant_lot:
                        #         if cql['lot_id'] == product_item_lot.lot_id.id:
                        #             cql['qty'] = cql['qty'] + product_item_lot.qty
                        #             qty = cql['qty']
                        # else:
                        #     list_lot_id.append(product_item_lot.lot_id.id)
                        #     check_quant_lot.append({
                        #         'lot_id': product_item_lot.lot_id.id,
                        #         'qty': product_item_lot.qty
                        #     })
                        #
                        # res = bundle_item.product_id.with_context(context)._product_available()
                        # if res[bundle_item.product_id.id]['qty_available'] < qty:
                        #     context = {'location': s.order_id.session_id.config_id.consign_location_id.id, }
                        #     res = bundle_item.product_id.with_context(context)._product_available()
                        #     if res[bundle_item.product_id.id]['qty_available'] < qty:
                        #         raise ValidationError("Lô %s của sản phẩm %s không đủ hàng (%s) trong kho %s" % (
                        #             product_item_lot.lot_id.name, bundle_item.product_id.name, res[bundle_item.product_id.id]['qty_available'],
                        #             s.order_id.location_id.name))

                        # check số lượng lot còn tồn:
                        # lấy tồn từ stock_quant để gắn lại vào 2 trường qty_inventory, qty_inventory_consign
                        check_qty = 0
                        query = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
                        self._cr.execute(query, (self.order_id.location_id.id, product_item_lot.lot_id.id))
                        qty_inventory = self._cr.dictfetchone()
                        if qty_inventory:
                            check_qty += qty_inventory['quantity']

                        query_consign = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
                        self._cr.execute(query_consign,
                                         (self.order_id.session_id.config_id.consign_location_id.id,
                                          product_item_lot.lot_id.id))
                        qty_inventory_consign = self._cr.dictfetchone()
                        if qty_inventory_consign:
                            check_qty += qty_inventory_consign['quantity']
                        if product_item_lot.qty > check_qty:
                            raise ValidationError("Lot %s này chỉ còn lại số lượng là %s!" % ( product_item_lot.lot_id.name ,check_qty,))

                        if check_qty == 0 :
                            raise ValidationError("Lot %s này hiện không còn. Vui lòng kiểm tra lại!!!!!" % ( product_item_lot.lot_id.name))

                        count_qty_lot += product_item_lot.qty
                    #check bằng số lượng thực xuất
                    if count_qty_lot != bundle_item.qty_export: raise ValidationError(
                        "Sản phẩm %s. Số lượng sản phẩm chọn trong lot phải bằng số lượng sản phẩm." % (bundle_item.product_id.name,))
                elif bundle_item.tracking_product == 'serial':
                    if len(bundle_item.product_item_lot_ids) != bundle_item.qty: raise ValidationError(
                        "Sản phẩm %s truy vết kiểu serial. Số lượng serial phải bằng số lượng bán." % (bundle_item.product_id.name,))
                    for product_item_lot in bundle_item.product_item_lot_ids:
                        if product_item_lot.lot_id.x_state != 'activated':
                            raise ValidationError("Mã lot/serial: %s bạn nhập trong sản phẩm %s không ở trạng thái đã kích hoạt" % (
                                product_item_lot.lot_id.name, bundle_item.product_id.name))
                        if product_item_lot.lot_id.life_date and product_item_lot.lot_id.life_date + timedelta(days=1) <= date_order:
                            raise ValidationError("Mã lot/serial: %s bạn nhập trong sản phẩm %s đã hết hạn" % (
                                product_item_lot.lot_id.name, bundle_item.product_id.name))
                        if bundle_item.product_id.type != 'consu':
                            context = {
                                'lot_id': product_item_lot.lot_id.id,
                                'location': s.order_id.location_id.id,
                            }
                            res = bundle_item.product_id.with_context(context)._product_available()
                            if res[bundle_item.product_id.id]['qty_available'] < 1:
                                context = {'location': s.order_id.session_id.config_id.consign_location_id.id, }
                                res = bundle_item.product_id.with_context(context)._product_available()
                                if res[bundle_item.product_id.id]['qty_available'] < 1:
                                    raise ValidationError("Serial %s của sản phẩm %s không đủ hàng (%s) trong kho %s" % (
                                        product_item_lot.lot_id.name, bundle_item.product_id.name, res[bundle_item.product_id.id]['qty_available'],
                                        s.order_id.location_id.name))
                        if product_item_lot.qty != 1: raise ValidationError(
                            "Sản phẩm %s truy vết kiểu serial. Chỉ chọn số lượng là 1" % (bundle_item.product_id.name,))
                else:
                    raise ValidationError(
                        "Sản phẩm %s có dạng truy vết là %s. Kiểm tra lại dữ liệu!" % s(bundle_item.product_id.name, bundle_item.tracking_product, ))

    # @api.multi
    # def action_save(self):
    #     if not self.x_location_id:
    #         self.x_location_id = self.order_id.location_id.id
    #     return True


class PosOrderProductItem(models.Model):
    _name = 'pos.order.product.item'

    order_line_id = fields.Many2one('pos.order.line', string="Order line")
    bundle_component_id = fields.Many2one('product.bundle.component', string="Bundle component")
    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure')
    qty = fields.Integer(string="Quantity")
    tracking_product = fields.Selection(related='product_id.tracking', string="Tracking product")
    product_item_lot_ids = fields.One2many('pos.order.product.item.lot', 'product_item_id', string="Item lot")
    revenue_rate = fields.Float(string='Revenue rate (%)')
#thêm đoạn để bán nợ sản phẩm
    qty_inventory = fields.Float("Qty inventory")  # số lượng tồn sản phẩm thực tế
    qty_inventory_consign = fields.Float("Qty inventory consign")  # số lượng tồn sản phẩm thực tế
    qty_export = fields.Float('Qty export')  # Số lượng thực xuất

    @api.onchange('qty_export')
    def _onchange_izi_pos_order_backorder(self):
        if self.product_id.type == 'product':
            if self.qty_export > self.qty_inventory + self.qty_inventory_consign:
                raise ValidationError("Số lượng thực xuất không được lớn hơn số lượng sản phẩm !!!!!!!!")
            if self.qty_export < 0 and not self.order_line_id.order_id.x_pos_partner_refund_id:
                raise ValidationError("Số lượng thực xuất không được âm !!!!!")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            for bundle_option in self.bundle_component_id.bundle_option_ids:
                if bundle_option.product_id == self.product_id:
                    self.uom_id = bundle_option.uom_id.id
                    self.qty = bundle_option.qty * self.order_line_id.qty
                    self.product_item_lot_ids = False
                    self.qty_inventory = self.env['stock.quant']._get_available_quantity(self.product_id,
                                                                                         self.order_line_id.order_id.session_id.config_id.stock_location_id)
                    self.qty_inventory_consign = self.env['stock.quant']._get_available_quantity(self.product_id,
                                                                                                 self.order_line_id.order_id.session_id.config_id.consign_location_id)

                    if self.qty > self.qty_inventory + self.qty_inventory_consign:
                        self.qty_export = self.qty_inventory
                    else:
                        self.qty_export = self.qty
                    if bundle_option.product_id.x_card_type != 'none':
                        self.qty_export = self.qty
                    break

        else:
            self.uom_id = False
            self.qty = 0
            self.product_item_lot_ids = False

    @api.constrains('product_id')
    def _check_product_id(self):
        for s in self:
            if not s.product_id:
                raise ValidationError("Bạn chưa chọn sản phẩm cho thành phần %s!" % (s.bundle_component_id.name,))

    @api.multi
    def action_input_lot(self):
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_order_id': self.id})
        view = self.sudo().env.ref('izi_product_bundle.pos_order_product_item_form_view')
        return {
            'name': "Product Item",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order.product.item',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.id,
            'target': 'new',
            'context': ctx,
        }


class PosOrderProductItemLot(models.Model):
    _name = 'pos.order.product.item.lot'

    product_item_id = fields.Many2one('pos.order.product.item', string='Product item')
    product_id = fields.Many2one(related='product_item_id.product_id', string="Product", readonly=1)
    tracking_product = fields.Selection(related='product_id.tracking', string="Tracking product", readonly=1)
    code_lot = fields.Char(string="Lot/serial code")
    qty = fields.Integer(string="Quantity")
    lot_id = fields.Many2one('stock.production.lot', string="Production lot")

    ''' tam thoi chua dung
    @api.onchange('code_lot')
    def _onchange_code_lot(self):
        if self.code_lot and self.product_id:
            ProductionLotObj = self.env['stock.production.lot']
            lot = ProductionLotObj.search([('name', '=ilike', str(self.code_lot).strip()), ('product_id', '=', self.product_id.id)], limit=1)
            if not lot:
                return {'warning': {'title': 'Thông báo', 'message': 'Không tìm thấy lot/serial có mã %s, của sản phẩm %s' % (str(self.code_lot), self.product_id.defaut_code, )}, 'lot_id': False}
            if self.product_id.x_card_type == 'none':
                if self.tracking_product == 'serial':
                    return {'lot_id': lot.id, 'qty': 1}
                return {'lot_id': lot.id}
            else:
                if lot.x_state != 'activated':
                    return {'warning': {'title': 'Thông báo', 'message': 'Chỉ bán thẻ ở trạng thái hiệu lực. \'%s\'' % (str(lot.x_state))}, 'lot_id': False}
                if lot.life_date < datetime.now().date():
                    return {'warning': {'title': 'Thông báo', 'message': 'Thẻ %s hết hạn vào ngày %s. Không thể bán!' % (self.code_lot, lot.life_date, )}, 'lot_id': False}
                if self.tracking_product == 'serial':
                    return {'lot_id': lot.id, 'qty': 1}
                return {'lot_id': lot.id}
        else:
            return {'lot_id': False}
    '''

    # @api.onchange('lot_id')
    # def _onchange_lot_id(self):
    #     if self.lot_id and self.tracking_product == 'serial':
    #         self.qty = 1
    #     if self.lot_id:
    #         check_qty = 0
    #         # lấy tồn từ stock_quant để gắn lại vào 2 trường qty_inventory, qty_inventory_consign
    #         query = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
    #         self._cr.execute(query, (self.product_item_id.order_line_id.order_id.location_id.id, self.lot_id.id))
    #         qty_inventory = self._cr.dictfetchone()
    #         if qty_inventory:
    #             check_qty += qty_inventory['quantity']
    #
    #         query_consign = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
    #         self._cr.execute(query_consign,
    #                          (self.product_item_id.order_line_id.order_id.session_id.config_id.consign_location_id.id,
    #                           self.x_lot_id.id))
    #         qty_inventory_consign = self._cr.dictfetchone()
    #         if qty_inventory_consign:
    #             check_qty += qty_inventory_consign['quantity']
    #
    #         if check_qty == 0 :
    #             raise ValidationError("Lot này hiện không còn. Vui lòng kiểm tra lại!!!!!")

    # @api.onchange('qty')
    # def onchange_qty(self):
    #     if self.qty and self.lot_id:
    #         check_qty = 0
    #         # lấy tồn từ stock_quant để gắn lại vào 2 trường qty_inventory, qty_inventory_consign
    #         query = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
    #         self._cr.execute(query, (self.product_item_id.order_line_id.order_id.location_id.id, self.lot_id.id))
    #         qty_inventory = self._cr.dictfetchone()
    #         if qty_inventory:
    #             check_qty += qty_inventory['quantity']
    #
    #         query_consign = '''select quantity from stock_quant where location_id = %s and lot_id = %s'''
    #         self._cr.execute(query_consign,
    #                          (self.product_item_id.order_line_id.order_id.session_id.config_id.consign_location_id.id, self.x_lot_id.id))
    #         qty_inventory_consign = self._cr.dictfetchone()
    #         if qty_inventory_consign:
    #             check_qty += qty_inventory_consign['quantity']
    #
    #         if self.qty > check_qty:
    #             raise ValidationError("Lot này chỉ còn lại số lượng là %s!" % (check_qty,))

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id and self.tracking_product == 'serial':
            self.qty = 1
