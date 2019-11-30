# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date

class PosMaterialRequest(models.Model):
    _name = 'pos.material.request'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char("Name", default='/', track_visibility='onchange')
    date = fields.Date("Date", track_visibility='onchange')
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    service_ids = fields.Many2many('product.product', string="Service", track_visibility='onchange')
    origin = fields.Char("Origin", track_visibility='onchange')
    use_service_id = fields.Many2one('pos.use.service', "Use service", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('wait_confirm', "Wait Confirm"), ('confirm', "Confirm"), ('done', "Done"),('done_refund', "Done Refund"), ('cancel', "Cancel")],
                             default='draft', track_visibility='onchange')
    material_request_ids = fields.One2many('pos.material.request.line', 'material_request_id', "Pos Material Request")
    picking_id = fields.Many2one('stock.picking', "Picking", track_visibility='onchange')
    picking_refund_id = fields.Many2one('stock.picking', "Picking Refund", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    location_id = fields.Many2one('stock.location', "Location")
    picking_type_id = fields.Many2one('stock.picking.type', "Stock Picking Type")
    company_id = fields.Many2one('res.company', "Company")
    branch_id = fields.Many2one('res.branch', string='Branch')
    force_available_field = fields.Boolean('Force Available Active')
    check_available_field = fields.Boolean('Check Available Active')
    type_request = fields.Selection([('normal', "Normal"), ('product', "Product")], default='normal')

    @api.multi
    def print_material_request(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_pos_use_service.pos_material_request_report_view_id/%s' % (
                self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.model
    def create(self, vals):
        res = super(PosMaterialRequest, self).create(vals)
        prefix = 'PXKHL'
        if res.type_request == 'product':
            prefix = 'PXKHB'
        sequence = self.env['ir.sequence'].next_by_code('pos.material.request') or _('New')
        res.name = prefix + '/' + sequence[6:]
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ("Không thể xóa bản ghi ở trang thái khác bản thảo"))
        return super(PosMaterialRequest, self).unlink()

    @api.multi
    def action_set_default_value(self):
        for line in self.material_request_ids:
            if line.replace_product_id:
                continue
            line.qty_use = line.qty


    @api.multi
    def action_confirm(self):
        if self.state != 'draft':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        for line in self.material_request_ids:
            if line.use == True:
                if line.qty_use == 0 and (line.replace_qty_use == 0 or not line.replace_product_id):
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập số lượng xuất cho NVL hoặc NVL thay thế cho nguyên vật liệu không còn là '+ line.product_id.name ))
                if line.replace_qty_use == 0 and line.replace_product_id:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập số lượng cho nguyên vật liệu thay thế là '+ line.replace_product_id.name))
        self.state = 'wait_confirm'

    @api.multi
    def check_available(self):
        if self.state != 'wait_confirm':
            return True
        count = 0
        for line in self.material_request_ids:
            if line.use is False:
                count += 1
            elif line.qty_use != 0:
                total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.location_id)
                line.qty_inventory = total_availability
                if line.qty_use <= total_availability:
                    line.state = 'ready'
                    count += 1
                else:
                    line.state = 'not_available'
            elif line.replace_qty_use != 0:
                total_availability = self.env['stock.quant']._get_available_quantity(line.replace_product_id, self.location_id)
                line.replace_qty_inventory = total_availability
                if line.replace_qty_use <= total_availability:
                    line.state = 'ready'
                    count += 1
                else:
                    line.state = 'not_available'
            for item in line.lot_lines:
                item._constraint_lot()
        if len(self.material_request_ids) == count:
            self.check_available_field = True
        else:
            self.check_available_field = False

    @api.multi
    def action_approval(self):
        if self.state != 'wait_confirm':
            return True
        self.check_available()
        if self.check_available_field == False:
            for line in self.material_request_ids:
                if line.use == True:
                    if line.qty_use != 0:
                        if line.qty_use > line.qty_inventory:
                            raise except_orm('Cảnh báo!',
                                             ('SL xuất lơn hơn SL tồn. Chi tiết liệu trình ' + line.name))
                    else:
                        if line.replace_qty_use > line.replace_qty_inventory:
                            raise except_orm('Cảnh báo!',
                                             ('SL xuất lơn hơn SL tồn. Chi tiết liệu trình ' + line.name))
        self.state = 'confirm'

    @api.multi
    def force_available(self):
        if self.state != 'wait_confirm':
            return True
        self.check_available()
        self.force_available_field = True
        self.state = 'confirm'


    @api.multi
    def action_done(self):
        if self.state != 'confirm':
            return True
        for line in self.material_request_ids:
            if line.show_details_visible == True and len(line.lot_lines) == 0:
                raise except_orm('Cảnh báo!',
                                 ('Vui lòng nhập số Lot/Serial cho sản phẩm ' + line.product_id.name))
        location_dest_id =  self.env.ref('stock.stock_location_customers')
        if self.picking_id.id == False or self.picking_id.state == 'cancel':
            picking_id = self._create_picking(self.picking_type_id.id, location_dest_id.id, self.location_id.id)
            if picking_id.id == False:
                raise except_orm(("Thông báo"), ("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'picking_id': picking_id.id})
        self.picking_id.action_confirm()
        self.picking_id.action_assign()
        if self.type_request == 'normal':
            if self.check_available_field == True:
                for line in self.picking_id.move_lines:
                    line.quantity_done = line.product_uom_qty
            else:
                for line in self.picking_id.move_lines:
                    if not len(line.move_line_ids):
                        stock_move_out_line_vals = {
                            'product_id': line.product_id.id,
                            'origin': self.name,
                            'product_uom_id': line.product_uom.id,
                            'qty_done': line.product_uom_qty,
                            'location_id': line.location_id.id,
                            'location_dest_id': line.location_dest_id.id,
                            'name': line.product_id.name,
                            'move_id': line.id,
                            'state': 'draft',
                            'picking_id': self.picking_id.id,
                        }
                        self.env['stock.move.line'].create(stock_move_out_line_vals)
                    else:
                        for move_line in line.move_line_ids:
                            move_line.qty_done = line.product_uom_qty
                            break
        else:
            for line in self.material_request_ids:
                if line.product_id.tracking == 'none':
                    if len(line.move_id.move_line_ids) != 0:
                        for m_line in line.move_id.move_line_ids:
                            if m_line.qty_done == 0:
                                m_line.qty_done = m_line.product_uom_qty
                    else:
                        stock_move_out_line_vals = {
                            'product_id': line.product_id.id,
                            'origin': self.name,
                            'product_uom_id': line.uom_id.id,
                            'qty_done': line.qty,
                            'location_id': self.location_id.id,
                            'location_dest_id': location_dest_id.id,
                            'name': line.product_id.name,
                            'move_id': line.move_id.id,
                            'state': 'draft',
                            'picking_id': self.picking_id.id,
                        }
                        self.env['stock.move.line'].create(stock_move_out_line_vals)
                else:
                    for item in line.lot_lines:
                        item.location_id = self.location_id.id
                        item.dest_location_id = location_dest_id.id
                        if all([x.lot_id != False and x.qty_done != 0 for x in line.move_id.move_line_ids]) or not len(line.move_id.move_line_ids):
                            stock_move_out_line_vals = {
                                'product_id': line.product_id.id,
                                'origin': self.name,
                                'product_uom_id': line.uom_id.id,
                                'qty_done': item.qty_done,
                                'location_id': self.location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'name': line.product_id.name,
                                'move_id': line.move_id.id,
                                'state': 'draft',
                                'picking_id': self.picking_id.id,
                                'lot_id': item.lot_id.id,
                                'lot_name': item.lot_id.name,
                            }
                            self.env['stock.move.line'].create(stock_move_out_line_vals)
                        else:
                            for move_line in line.move_id.move_line_ids:
                                if move_line.qty_done == 0 or not move_line.lot_id:
                                    move_line.qty_done = item.qty_done
                                    move_line.lot_id = item.lot_id.id
                                    move_line.lot_name = item.lot_id.name
                                    break
            for line in self.material_request_ids:
                if line.product_id.tracking != 'none':
                    if line.qty_done < line.qty_use:
                        raise except_orm(_('Thông báo'), _(
                            'Bạn chưa nhập đủ chi tiết số lô/serial cho sản phẩm "%s". Vui lòng cập nhật thêm để hoàn thành đơn!' % line.product_id.name))
                    elif line.qty_done > line.qty_use:
                        raise except_orm(_('Thông báo'), _(
                            'Bạn đã nhập chi tiết số lô/serial lớn hơn số lượng dịch chuyển ban đầu. Chi tiết sản phẩm "%s".' % line.product_id.name))
        self.picking_id.button_validate()
        self.state = 'done'
        self.use_service_id.state = 'working'

    @api.multi
    def _create_picking(self, picking_type_id, location_dest_id, location_id):
        StockPicking = self.env['stock.picking']
        picking = False
        for item in self:
            if any([ptype in ['product', 'consu'] for ptype in item.material_request_ids.mapped('product_id.type')]):
                res = item._prepare_picking(picking_type_id, location_dest_id, location_id)
                picking = StockPicking.create(res)
                item.material_request_ids._create_stock_moves(picking)
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': item},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
        return {
            'picking_type_id': picking_type_id,
            'partner_id': self.use_service_id.partner_id.id,
            'date': self.date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.use_service_id.company_id.id,
            'branch_id': self.use_service_id.branch_id.id
        }

    @api.multi
    def action_refund(self):
        if self.state != 'done':
            return True
        location_id =  self.env.ref('stock.stock_location_customers')
        location_dest_id =  self.location_id
        if self.picking_refund_id.id == False or self.picking_refund_id.state == 'cancel':
            picking_id = self._create_picking(self.picking_type_id.id, location_dest_id.id, location_id.id)
            if picking_id.id == False:
                raise except_orm(("Thông báo"), ("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'picking_refund_id': picking_id.id})
        self.picking_refund_id.action_confirm()
        self.picking_refund_id.action_assign()
        if self.type_request == 'normal':
            for line in self.picking_refund_id.move_lines:
                line.quantity_done = line.product_uom_qty
        else:
            for line in self.material_request_ids:
                if line.product_id.tracking == 'none':
                    if len(line.move_refund_id.move_line_ids) != 0:
                        for m_line in line.move_refund_id.move_line_ids:
                            if m_line.qty_done == 0:
                                m_line.qty_done = m_line.product_uom_qty
                    else:
                        stock_move_out_line_vals = {
                            'product_id': line.product_id.id,
                            'origin': self.name,
                            'product_uom_id': line.uom_id.id,
                            'qty_done': line.qty,
                            'location_id': location_id.id,
                            'location_dest_id': location_dest_id.id,
                            'name': line.product_id.name,
                            'move_id': line.move_id.id,
                            'state': 'draft',
                            'picking_id': self.picking_refund_id.id,
                        }
                        self.env['stock.move.line'].create(stock_move_out_line_vals)
                else:
                    for item in line.lot_lines:
                        item.location_id = location_id.id
                        item.dest_location_id = location_dest_id.id
                        if all([x.lot_id != False and x.qty_done != 0 for x in line.move_refund_id.move_line_ids]) or not len(line.move_refund_id.move_line_ids):
                            stock_move_out_line_vals = {
                                'product_id': line.product_id.id,
                                'origin': self.name,
                                'product_uom_id': line.uom_id.id,
                                'qty_done': item.qty_done,
                                'location_id': location_id.id,
                                'location_dest_id': location_dest_id.id,
                                'name': line.product_id.name,
                                'move_id': line.move_id.id,
                                'state': 'draft',
                                'picking_id': self.picking_refund_id.id,
                                'lot_id': item.lot_id.id,
                                'lot_name': item.lot_id.name,
                            }
                            self.env['stock.move.line'].create(stock_move_out_line_vals)
                        else:
                            for move_line in line.move_refund_id.move_line_ids:
                                if move_line.qty_done == 0 or not move_line.lot_id:
                                    move_line.qty_done = item.qty_done
                                    move_line.lot_id = item.lot_id.id
                                    move_line.lot_name = item.lot_id.name
                                    break
        self.picking_refund_id.button_validate()
        self.state = 'done_refund'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

class PosMaterialRequestLine(models.Model):
    _name = 'pos.material.request.line'

    sequence = fields.Integer('Sequence LT')
    name = fields.Char('Name LT')
    product_id = fields.Many2one('product.product', "Product",domain=[('type', '!=', 'service')])
    qty = fields.Float("Qty")
    qty_use = fields.Float("Quantity Use")
    qty_done = fields.Float('Qty Done',compute='_compute_qty_done')
    uom_id = fields.Many2one('uom.uom', 'Product Uom')
    qty_inventory = fields.Float('Quantity Remain Stock')
    replace_product_id = fields.Many2one('product.product', "Replace Product", domain=[('type', '!=', 'service')])
    replace_qty_use = fields.Float("Replace Qty")
    replace_uom_id = fields.Many2one('uom.uom', 'Replace Uom')
    replace_qty_inventory = fields.Float("Replace Qty Inventory")
    state = fields.Selection([('ready', "Ready"), ('not_available', "Not Available"),('stock_out', "Stock Out")])
    use = fields.Boolean("Use", default=True)
    material_request_id = fields.Many2one('pos.material.request', 'Use Material')

    show_details_visible = fields.Boolean('Details Visible', compute='_compute_show_details_visible')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    move_refund_id = fields.Many2one('stock.move', string='Stock Move refund')
    lot_lines = fields.One2many('pos.material.request.lot.line', 'material_line_id', string='Material lot')

    @api.depends('lot_lines')
    def _compute_qty_done(self):
        for item in self:
            total = 0
            if item.product_id.tracking != 'none':
                if len(item.lot_lines):
                    for tmp in item.lot_lines:
                        if tmp.lot_id and tmp.qty_done:
                            total += tmp.qty_done
                item.qty_done = total
            else:
                if item.material_request_id.state == 'done':
                    item.qty_done = item.qty

    @api.depends('product_id')
    def _compute_show_details_visible(self):
        for item in self:
            if not item.product_id:
                item.show_details_visible = False
            else:
                if item.product_id.tracking != 'none':
                    item.show_details_visible = True
                else:
                    item.show_details_visible = False

    @api.onchange('replace_product_id')
    def onchange_uom_replace(self):
        self.replace_uom_id = self.replace_product_id.product_tmpl_id.uom_id.id

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.product_tmpl_id.uom_id.id

    def _create_stock_moves(self, picking):
        moves = self.env['stock.move']
        for line in self:
            if line.use == True:
                vals = line._prepare_stock_moves(picking)
                move_id = moves.create(vals)
                if not line.move_id:
                    line.move_id = move_id.id
                else:
                    line.move_refund_id = move_id.id

    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        if self.qty_use != 0:
            product_id = self.product_id
            product_uom = self.uom_id
            qty = self.qty_use
        else:
            product_id = self.replace_product_id
            product_uom = self.replace_uom_id
            qty = self.replace_qty_use
        template = {
            'name': self.name or '',
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty,
            'date': picking.date,
            'date_expected': self.material_request_id.date,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'state': 'draft',
            'company_id': picking.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.material_request_id.name
        }
        return template


    @api.multi
    def action_show_details(self):
        location_dest_id = self.env.ref('stock.stock_location_customers')
        ctx = self.env.context.copy()
        ctx.update({'loca_id': self.material_request_id.location_id.id, 'loca_dest_id': location_dest_id.id})
        view = self.env.ref('izi_pos_use_service.pos_material_request_lot_line_tree_view')
        return {
            'name': _('Add lot'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.material.request.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }


class PosMaterialRequestLotLine(models.Model):
    _name = 'pos.material.request.lot.line'

    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'From')
    dest_location_id = fields.Many2one('stock.location', 'To')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    lot_name = fields.Char('Lot/Serial Number Name')
    life_date = fields.Date(string='Life Date', compute='_compute_life_date')
    qty_done = fields.Float('Qty Done')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    material_line_id = fields.Many2one('pos.material.request.line', 'Material line')

    @api.depends('lot_id')
    def _compute_life_date(self):
        for item in self:
            if item.lot_id:
                item.life_date = item.lot_id.life_date

    def _constraint_lot(self):
        if self.lot_id and self.qty_done > 0:
            total_availability = self.env['stock.quant']._get_available_quantity(self.product_id, self.location_id,lot_id=self.lot_id)
            if total_availability < self.qty_done:
                raise except_orm(_('Thông báo'), _('Lot/Serial Number không đủ hàng trong địa điểm xuất hàng. Chi tiết mã "'+ self.lot_id.name +'"'))



