# -*- coding: utf-8 -*-

# author: HoiHD , file này chứa các action trong luồng phát hành thẻ

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import except_orm
from datetime import date, datetime


class ProductReleaseInherit(models.Model):
    _inherit = 'product.release'

    def _get_inventory(self, product_id, location_id):
        # Lấy số lượng tồn kho của 1 sản phẩm tại 1 địa điểm cho sẵn
        total_availability = self.env['stock.quant']._get_available_quantity(product_id, location_id)
        return total_availability

    # Sinh mã theo quy tắc
    def _generate_code(self, qty):
        # Kiểm tra số với tiền tố mã thẻ hiện tại, nếu tồn tại thì sinh mã với số tự tăng tiếp nối
        # Ngược lại sinh mới từ 1
        list_code = []
        prefix = ""
        month = self.date.month
        release_reason = str(self.release_reason_id.code)
        receive_unit_code = str(self.branch_id.code)
        if self.card_id.product_tmpl_id.type == 'product':
            prefix = 'p'
        if self.card_id.product_tmpl_id.type == 'consu':
            prefix = 'e'

        code = prefix + release_reason + receive_unit_code + str(self.date.year)[2:] + (str(month) if month > 10 else '0' + str(month))

        query = """SELECT l.name as code FROM stock_production_lot l
                            WHERE l.name like %s
                            ORDER BY l.name desc LIMIT 1"""
        self._cr.execute(query, (str(code + '%'),))
        new_code = self._cr.fetchall()
        for i in range(0, qty):
            stt = i + 1
            if len(new_code) == 0:
                len_stt = len(str(stt))
                auto = '0' * (6 - len_stt) + str(stt)
            else:
                code_max = new_code[0][0][-6:]
                int_new = int(code_max) + stt
                str_new = len(str(int_new))
                auto = '0' * (6 - str_new) + str(int_new)
            list_code.append(code + auto)
        return list_code

    # Sinh mã cho đợt phát hành
    @api.multi
    def generate_serial(self):
        if self.state != 'draft':
            return True
        if self.quantity <= 0:
            raise except_orm('Thông báo', 'Nhập số lượng phát hành lớn hơn 0.')
        list_production = []
        self.stock_production_lot_ids = False
        list_code = self._generate_code(self.quantity)
        for i in range(0, self.quantity):
            code = list_code[i]
            vals = {
                'name': code,
                'x_release_id': self.id,
                'product_id': self.card_id.id,
                'product_uom_id': self.card_id.product_tmpl_id.uom_id.id,
                'x_extend_date': False,
                'x_customer_id': False,
                'x_use_customer_id': False,
                'x_branch_id': self.location_id.branch_id.id,
            }
            list_production.append(vals)
        self.stock_production_lot_ids = list_production
        self.state = 'created'

    @api.multi
    def action_active(self):
        if self.state != 'created':
            return True
        # mới sửa, kiểm tra phôi, nếu không có phôi thì không kiểm kho
        if self.blank_card_id:
            total_blank_card = self._get_inventory(self.blank_card_id, self.release_location_id)
            if total_blank_card < self.quantity:
                raise except_orm('Thông báo', 'Không đủ tồn kho phôi bạn chọn.')
        if self.card_id.type == 'product':
            self.do_transfer_loss()
        if self.expired_type == 'fixed':
            life_date = self.expired_date
        else:
            life_date = False
        for serial in self.stock_production_lot_ids:
            serial.write({'x_state': 'activated',
                          'x_company_id': self.company_id.id,
                          'x_total_count': self.card_id.x_card_count if self.card_id.x_card_type != 'voucher' else 1,
                          'life_date': life_date})
        if self.release_location_id.id == self.location_id.id or self.location_id.id is False:
            self.state = 'done'
        else:
            self.state = 'activated'

    @api.multi
    def do_transfer_loss(self):
        product_vals = self._get_inventory_loss(self.blank_card_id)
        property_stock_inventory = product_vals.get('property_stock_inventory')
        product_vals_in = self._get_inventory_loss(self.card_id)
        property_stock_production_in = product_vals_in.get('property_stock_inventory')

        release_stock = self.release_location_id
        cost_price_out = product_vals.get('cost_price', 0.0)
        cost_price_in = product_vals_in.get('cost_price', 0.0)
        move_obj = self.env['stock.move']
        move_line_obj = self.env['stock.move.line']
        Picking_obj = self.env['stock.picking']
        warehouse_id = self.env['stock.warehouse'].search([('view_location_id', '=', release_stock.location_id.id)], limit=1)
        picking_out_id = warehouse_id.out_type_id.id
        picking_in_id = warehouse_id.in_type_id.id

        # Thực hiện xuất phôi từ kho phát hành về kho ảo tồn kho, kiểu giao nhận là giao hàng(out_type_id)
        # Kho ảo tồn kho được lấy từ trong sản phẩm
        # chính là địa điểm kiểm kê trong nhóm địa điểm đối ứng.
        # Thực hiện việc xuất phôi từ kho phát hành đến kho ảo của sản phẩm để kiểm kê số lượng và giá gốc của sản phẩm đó
        picking_out_vals = {
            'picking_type_id': picking_out_id,
            'date': date.today(),
            'origin': self.name,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_inventory,
            'state': 'done',
            'partner_id': self.location_id.partner_id.id,
            'x_product_release_id': self.id,
            'branch_id': self.branch_id.id,
        }
        picking_out_id = Picking_obj.create(picking_out_vals)
        stock_move_out_vals = {
            'product_id': self.blank_card_id.id,
            'origin': self.name,
            'product_uom': self.blank_card_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_out,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_inventory,
            'name': self.blank_card_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id,
            'picking_id': picking_out_id.id,
            'branch_id': self.branch_id.id,
        }
        move_out = move_obj.create(stock_move_out_vals)
        stock_move_out_line_vals = {
            'product_id': self.blank_card_id.id,
            'origin': self.name,
            'product_uom_id': self.blank_card_id.product_tmpl_id.uom_id.id,
            'qty_done': self.quantity,
            'price_unit': cost_price_out,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_inventory,
            'name': self.blank_card_id.product_tmpl_id.name,
            'move_id': move_out.id,
            'state': 'done',
            'picking_id': picking_out_id.id,
        }
        move_line_obj.create(stock_move_out_line_vals)

        # Thực hiện nhập thẻ từ kho ảo sản xuất vào kho phát hành
        # sau khi xuất phôi từ kho phát hành sang kho ảo,
        # bên kho ảo sẽ thực hiện kiểm kê và in thẻ
        # rồi sau đó lại xuất thẻ đã được in từ phôi sang kho phát hành
        picking_in_vals = {
            'picking_type_id': picking_in_id,
            'date': date.today(),
            'origin': self.name,
            'location_id': property_stock_production_in,
            'location_dest_id': release_stock.id,
            'state': 'done',
            'partner_id': self.location_id.partner_id.id,
            'x_product_release_id': self.id,
            'branch_id': self.branch_id.id,
        }
        picking_in_id = Picking_obj.create(picking_in_vals)
        stock_move_in_vals = {
            'product_id': self.card_id.id,
            'origin': self.name,
            'product_uom': self.card_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_in,
            'location_id': property_stock_production_in,
            'location_dest_id': release_stock.id,
            'name': self.card_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id,
            'picking_id': picking_in_id.id,
            'branch_id': self.branch_id.id,
        }
        move_in = move_obj.create(stock_move_in_vals)
        for ob in self.stock_production_lot_ids:
            stock_move_in_line_vals = {
                'product_id': self.card_id.id,
                'origin': self.name,
                'product_uom_id': self.card_id.product_tmpl_id.uom_id.id,
                'qty_done': 1,
                'price_unit': cost_price_in,
                'location_id': property_stock_production_in,
                'location_dest_id': release_stock.id,
                'name': self.card_id.product_tmpl_id.name,
                'lot_id': ob.id,
                'lot_name': ob.name,
                'move_id': move_in.id,
                'state': 'done',
                'picking_id': picking_in_id.id,
            }
            move_line_obj.create(stock_move_in_line_vals)
        return True

    # Hàm này sẽ vào trong mục kho của sản phẩm
    # sau đó lấy ra địa điểm ảo kiểm kê làm địa điểm để cho phôi thẻ vào và in thẻ tại đó
    # lấy giá vốn của sản phẩm
    def _get_inventory_loss(self, product_id):
        if not product_id.property_stock_inventory:
            raise except_orm('Error!', 'Bạn cần phải cấu hình Địa điểm kiểm kê: Chọn Sản phẩm --> Vào tab Kho --> Trong mục Địa điểm đối ứng --> Chọn Địa điểm kiểm kê')
        property_stock_inventory = product_id.property_stock_inventory.id
        cost_price = product_id.standard_price
        dict = {
            'property_stock_inventory': property_stock_inventory,
            'cost_price': cost_price
        }
        return dict

    @api.multi
    def action_transfer(self):
        if self.state != 'activated':
            return True
        # Xét TH cùng 1 location thì chuyển trạng thái về done
        if self.release_location_id == self.location_id:
            self.write({'state': 'done'})
        else:
            # Cùng 1 WH, tạo 1 stock_picking và picking_type là internal
            if self.release_location_id.location_id.id == self.location_id.location_id.id:
                picking_obj = self.env['stock.picking']
                stock_move_obj = self.env['stock.move']
                stock_move_line_obj = self.env['stock.move.line']
                warehouse_id = self.env['stock.warehouse'].search([
                    ('view_location_id', '=', self.release_location_id.location_id.id)], limit=1)
                # Tạo 1 stock_picking với picking_type là dịch chuyển nội bộ, lấy từ WH
                stock_picking_values = {
                    'picking_type_id': warehouse_id.int_type_id.id,
                    'date': date.today(),
                    'partner_id': self.location_id.partner_id.id,
                    'origin': self.name,
                    'location_id': self.release_location_id.id,
                    'location_dest_id': self.location_id.id,
                    'x_product_release_id': self.id,
                    'state': 'done',
                    'branch_id': self.branch_id.id,
                }
                stock_picking_id = picking_obj.create(stock_picking_values)
                stock_move_values = {
                    'product_id': self.card_id.id,
                    'origin': self.name,
                    'product_uom': self.card_id.product_tmpl_id.uom_id.id,
                    'product_uom_qty': self.quantity,
                    'location_id': self.release_location_id.id,
                    'location_dest_id': self.location_id.id,
                    'name': self.card_id.product_tmpl_id.name,
                    'state': 'draft',
                    'picking_id': stock_picking_id.id,
                    'branch_id': self.branch_id.id,
                }
                stock_move_id = stock_move_obj.create(stock_move_values) # tao 1 stock_move
                for line in self.stock_production_lot_ids:
                    stock_move_line_values = {
                        'product_id': self.card_id.id,
                        'origin': self.name,
                        'product_uom_id': self.card_id.product_tmpl_id.uom_id.id,
                        'qty_done': 1,
                        'location_id': self.release_location_id.id,
                        'location_dest_id': self.location_id.id,
                        'name': self.card_id.product_tmpl_id.name,
                        'lot_id': line.id,
                        'lot_name': line.name,
                        'move_id': stock_move_id.id,
                        'picking_id': stock_picking_id.id,
                    }
                    stock_move_line_obj.create(stock_move_line_values)
                stock_picking_id.action_confirm()
                stock_picking_id.action_assign()
                stock_picking_id.button_validate()
                self.write({'state': 'done', 'picking_id': stock_picking_id.id})
            # khác WH thì dùng stock_transfer để chuyển giữa  các WH
            else:
                stock_transfer = self.env['stock.transfer']
                stock_transfer_line = self.env['stock.transfer.line']
                stock_warehouse_id = self.env['stock.warehouse'].search([
                                                    ('view_location_id', '=', self.release_location_id.location_id.id)], limit=1)
                stock_dest_warehouse_id = self.env['stock.warehouse'].search([
                                                    ('view_location_id', '=', self.location_id.location_id.id)], limit=1)

                # tạo 1 stock_transfer
                stock_transfer_values = {
                    'warehouse_id': stock_warehouse_id.id,
                    'dest_warehouse_id': stock_dest_warehouse_id.id,
                    'location_id': self.release_location_id.id,
                    'dest_location_id': self.location_id.id,
                    'scheduled_date': date.today(),
                    'state': 'draft',
                    'origin': self.name,
                }
                stock_transfer_id = stock_transfer.create(stock_transfer_values)
                # tao 1 stock_transfer_line
                stock_transfer_line_values = {
                    'product_id': self.card_id.id,
                    'quantity_from': self.quantity,
                    'stock_transfer_id': stock_transfer_id.id,
                    'product_uom': self.card_id.product_tmpl_id.uom_id.id,
                    'note': '',
                    'state': 'draft',
                }
                stock_transfer_line_id = stock_transfer_line.create(stock_transfer_line_values)
                stock_transfer_id.action_confirm()
                stock_transfer_id.action_assign()
                new_arr = []
                for in_line in self.stock_production_lot_ids:
                    obj = {
                        'lot_id': in_line.id,
                        'lot_name': in_line.name,
                        'qty_done': 1,
                    }
                    new_arr.append(obj)
                index = 0
                for item in stock_transfer_id.picking_from_id.move_line_ids:
                    item.update(new_arr[index])
                    index += 1
                stock_transfer_id.action_transfer()
                self.write({'state': 'transferring', 'picking_id': stock_transfer_id.picking_from_id.id})

    @api.multi
    def action_cancel_release(self):
        if self.state == 'activated' and self.card_blank_id:
            self.do_transfer()
        for ob in self.production_lot_ids:
            ob.unlink()
        self.write({'state': 'done'})

    @api.multi
    def do_transfer(self):
        product_vals = self._get_inventory_loss(self.blank_card_id)
        property_stock_inventory = product_vals.get('property_stock_inventory')
        product_vals_in = self._get_inventory_loss(self.card_id)
        property_stock_production_in = product_vals.get('property_stock_production')

        release_stock = self.release_location_id
        cost_price_out = product_vals.get('cost_price', 0.0)
        cost_price_in = product_vals_in.get('cost_price', 0.0)
        move_obj = self.env['stock.move']
        move_line_obj = self.env['stock.move.line']
        Picking_obj = self.env['stock.picking']
        warehouse_id = self.env['stock.warehouse'].search([
            ('view_location_id', '=', release_stock.location_id.id)
        ], limit=1)
        picking_out_id = warehouse_id.out_type_id.id
        picking_in_id = warehouse_id.in_type_id.id

        # Thực hiện trả phôi từ kho ảo tồn kho về kho nguồn
        picking_in_vals = {
            'picking_type_id': picking_in_id,
            'date': date.today(),
            'origin': self.name,
            'location_id': property_stock_inventory,
            'location_dest_id': release_stock.id,
            'state': 'done',
            'x_product_release_id': self.id,
            'branch_id': self.branch_id.id,
        }
        picking_in_id = Picking_obj.create(picking_in_vals)
        stock_move_out_vals = {
            'product_id': self.blank_card_id.id,
            'origin': self.name,
            'product_uom': self.blank_card_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_out,
            'location_dest_id': release_stock.id,
            'location_id': property_stock_inventory,
            'name': self.blank_card_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id,
            'picking_id': picking_in_id.id,
            'branch_id': self.branch_id.id,
        }
        move_out = move_obj.create(stock_move_out_vals)
        stock_move_out_line_vals = {
            'product_id': self.blank_card_id.id,
            'origin': self.name,
            'product_uom_id': self.blank_card_id.product_tmpl_id.uom_id.id,
            'qty_done': self.quantity,
            'price_unit': cost_price_out,
            'location_dest_id': release_stock.id,
            'location_id': property_stock_inventory,
            'name': self.blank_card_id.product_tmpl_id.name,
            'move_id': move_out.id,
            'state': 'done',
            'picking_id': picking_in_id.id,
        }
        move_line_obj.create(stock_move_out_line_vals)

        # Thực hiện trả thẻ từ kho phát hành về kho ảo sản xuất
        picking_out_vals = {
            'picking_type_id': picking_out_id,
            'date': date.today(),
            'origin': self.name,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_production_in,
            'state': 'done',
            'x_product_release_id': self.id,
            'branch_id': self.branch_id.id,
        }
        picking_out_id = Picking_obj.create(picking_out_vals)
        stock_move_in_vals = {
            'product_id': self.card_id.id,
            'origin': self.name,
            'product_uom': self.card_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_in,
            'location_dest_id': property_stock_production_in,
            'location_id': release_stock.id,
            'name': self.card_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id,
            'picking_id': picking_out_id.id,
            'branch_id': self.branch_id.id,
        }
        move_in = move_obj.create(stock_move_in_vals)
        for ob in self.production_lot_ids:
            stock_move_in_line_vals = {
                'product_id': self.card_id.id,
                'origin': self.name,
                'product_uom_id': self.card_id.product_tmpl_id.uom_id.id,
                'qty_done': 1,
                'price_unit': cost_price_in,
                'location_dest_id': property_stock_production_in,
                'location_id': release_stock.id,
                'name': self.card_id.product_tmpl_id.name,
                'lot_id': ob.id,
                'lot_name': ob.name,
                'move_id': move_in.id,
                'state': 'done',
                'picking_id': picking_out_id.id,
            }
            move_line_obj.create(stock_move_in_line_vals)
        return True
