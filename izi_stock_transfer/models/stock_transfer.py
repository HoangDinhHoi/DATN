# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64


class StockTransfer(models.Model):
    _name = 'stock.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Transfer Code', track_visibility='onchange', default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', string='Source Branch', track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse', track_visibility='onchange')
    location_id = fields.Many2one('stock.location', 'Source Location', track_visibility='onchange')
    dest_branch_id = fields.Many2one('res.branch', string='Destination Branch', track_visibility='onchange')
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'Destination Warehouse', track_visibility='onchange')
    dest_location_id = fields.Many2one('stock.location', 'Destination Location', track_visibility='onchange')
    picking_from_id = fields.Many2one('stock.picking', 'Stock picking from')
    picking_to_id = fields.Many2one('stock.picking', 'Stock picking to')

    x_compute_wh = fields.Boolean(compute='_compute_wh')
    transfer_line_ids = fields.One2many('stock.transfer.line', 'stock_transfer_id', 'Operations', track_visibility='onchange')

    scheduled_date = fields.Datetime('Scheduled Date', track_visibility='onchange', default=fields.Datetime.now)
    origin = fields.Char('Source document', track_visibility='onchange')
    note = fields.Text('Note')
    state = fields.Selection([('draft', 'Draft'), ('not_available', 'Not Available'),
                              ('ready', 'Ready'), ('transfer', 'Transfer'),('done', 'Done'), ('cancel', 'Cancel')], 'State',
                             track_visibility='onchange', default="draft")
    date_receive = fields.Datetime('Received Date')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Reference')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")
    account_move_id = fields.Many2one('account.move', 'Account Move')
    dest_account_move_id = fields.Many2one('account.move', 'Dest Account Move')

    def _create_account_move(self):
        if not self.branch_id:
            raise UserError(
                _("Chưa cấu hình chi nhánh cho kho " + self.warehouse_id.name))
        if len(self.transfer_line_ids) > 0:
            move_lines = []
            journal_id = False
            for line in self.transfer_line_ids:
                if not line.product_id.product_tmpl_id.categ_id.x_account_transfer_id:
                    raise UserError(
                        _("Chưa cấu hình tài khoản chuyển kho cho nhóm " + line.product_id.product_tmpl_id.categ_id.name))
                journal_id = line.product_id.product_tmpl_id.categ_id.property_stock_journal
                debit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.scheduled_date.date(),
                    'account_id': line.product_id.product_tmpl_id.categ_id.x_account_transfer_id.id,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'debit': line.qty*line.product_id.standard_price,
                    'credit': 0.0,
                    'branch_id': self.branch_id.id
                }
                move_lines.append((0, 0, debit_move_vals))

                # Ghi sổ thu/chi của công ty
                credit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.scheduled_date.date(),
                    'account_id': line.product_id.product_tmpl_id.categ_id.property_stock_valuation_account_id.id,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'credit': line.qty*line.product_id.standard_price,
                    'debit': 0.0,
                    'branch_id' : self.branch_id.id
                }
                move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': self.name,
                'date': self.scheduled_date.date(),
                'journal_id': journal_id.id,
                'line_ids': move_lines,
                'branch_id': self.branch_id.id
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            self.account_move_id = move_id

    def _create_dest_account_move(self):
        if not self.dest_branch_id:
            raise UserError(
                _("Chưa cấu hình chi nhánh cho kho" + self.dest_warehouse_id.name))
        if len(self.transfer_line_ids) > 0:
            move_lines = []
            journal_id = False
            for line in self.transfer_line_ids:
                if not line.product_id.product_tmpl_id.categ_id.x_account_transfer_id:
                    raise UserError(
                        _("Chưa cấu hình tài khoản chuyển kho cho nhóm " + line.product_id.product_tmpl_id.categ_id.name))
                journal_id = line.product_id.product_tmpl_id.categ_id.property_stock_journal
                debit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.date_receive.date(),
                    'account_id': line.product_id.product_tmpl_id.categ_id.property_stock_valuation_account_id.id,
                    'quantity': line.qty_done if line.qty_done != 0 else line.qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'debit': line.qty_done*line.product_id.standard_price if line.qty_done != 0 else line.qty*line.product_id.standard_price,
                    'credit': 0.0,
                    'branch_id': self.dest_branch_id.id
                }
                move_lines.append((0, 0, debit_move_vals))

                # Ghi sổ thu/chi của công ty
                credit_move_vals = {
                    'name': self.name,
                    'ref': self.name,
                    'date': self.date_receive.date(),
                    'account_id': line.product_id.product_tmpl_id.categ_id.x_account_transfer_id.id,
                    'quantity': line.qty_done if line.qty_done != 0 else line.qty,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'credit': line.qty_done*line.product_id.standard_price if line.qty_done != 0 else line.qty*line.product_id.standard_price,
                    'debit': 0.0,
                    'branch_id': self.branch_id.id
                }
                move_lines.append((0, 0, credit_move_vals))
            move_vals = {
                'ref': self.name,
                'date': self.date_receive.date(),
                'journal_id': journal_id.id,
                'line_ids': move_lines,
                'branch_id': self.dest_branch_id.id
            }
            move_id = self.env['account.move'].create(move_vals)
            move_id.post()
            self.dest_account_move_id = move_id

    @api.depends('dest_warehouse_id', 'warehouse_id')
    def _compute_wh(self):
        for item in self:
            if not item.warehouse_id or not item.dest_warehouse_id or item.warehouse_id.id != item.dest_warehouse_id.id:
                item.x_compute_wh = False
            else:
                item.x_compute_wh = True

    @api.onchange('purchase_id')
    def _onchange_purchase(self):
        if self.purchase_id:
            tmp = []
            self.transfer_line_ids = False
            for line in self.purchase_id.order_line:
                if line.product_id.type in ('consu','product'):
                    argv = {
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom.id,
                        'qty': line.product_qty,
                        'name': line.name,
                    }
                    tmp.append(argv)
            self.transfer_line_ids = tmp
            self.origin = str(self.purchase_id.name)
            self.purchase_id = False

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.branch_id = self.warehouse_id.branch_id.id

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_id(self):
        if self.dest_warehouse_id:
            self.dest_branch_id = self.dest_warehouse_id.branch_id.id

    def _check_available(self):
        check_available = 0
        for line in self.transfer_line_ids:
            total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.location_id)
            if total_availability <= 0:
                line.qty_available = 'Không có hàng'
                check_available += 1
            elif total_availability < line.qty:
                line.qty_available = 'Tồn: ' + str(total_availability) + ' - Không đủ hàng'
                check_available += 1
            else:
                line.qty_available = 'Đủ hàng'
        if check_available != 0:
            return 'not_available'
        return 'ready'

    @api.multi
    def action_confirm(self):
        if self.state not in ('draft', 'not_available'):
            return True
        if len(self.transfer_line_ids) == 0:
            raise UserError(_('Không có chi tiết dịch chuyển'))
        for line in self.transfer_line_ids:
            if line.qty == 0:
                raise UserError(_('Bạn chưa nhập số lượng cần xuất'))
        check_available = self._check_available()
        if check_available == 'not_available':
            self.state = 'not_available'
            return True
        picking_type_from_id = self.warehouse_id.int_type_id
        if self.warehouse_id.id == self.dest_warehouse_id.id:
            if self.location_id.id == self.dest_location_id.id:
                raise UserError(_("Vui lòng chọn 2 địa điểm kho khác nhau!"))
            dest_location_id = self.dest_location_id
        else:
            if self.dest_warehouse_id.x_wh_transfer_loc_id.id == False:
                raise UserError(_("Chưa cấu hình địa điểm trung chuyển hàng hóa trong kho. Xin hãy liên hệ với người quản trị"))
            dest_location_id = self.dest_warehouse_id.x_wh_transfer_loc_id
        if self.picking_from_id.id == False or self.picking_from_id.state == 'cancel':
            picking_id = self._create_picking(picking_type_from_id.id, dest_location_id.id, self.location_id.id, self.branch_id.id)
            if picking_id.id == False:
                raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'picking_from_id': picking_id.id})
        self.state = 'ready'

    @api.multi
    def _create_picking(self, picking_type_id, location_dest_id, location_id, branch_id, check_transfer=True):
        StockPicking = self.env['stock.picking']
        picking = False
        for transfer in self:
            if any([ptype in ['product', 'consu'] for ptype in transfer.transfer_line_ids.mapped('product_id.type')]):
                res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id, branch_id)
                picking = StockPicking.create(res)
                moves = transfer.transfer_line_ids._create_stock_moves(picking, check_transfer)
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': transfer},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id, branch_id):
        return {
            'picking_type_id': picking_type_id,
            'date': self.scheduled_date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
            'branch_id': branch_id,
        }

    @api.multi
    def action_transfer(self):
        if self.state != 'ready':
            return True
        check_available = self._check_available()
        if check_available == 'not_available':
            self.state = 'not_available'
            return True
        for line in self.transfer_line_ids:
            if line.product_id.tracking != 'none':
                for item in line.lot_lines:
                    item._constraint_lot()
        self.picking_from_id.action_confirm()
        self.picking_from_id.action_assign()
        for line in self.transfer_line_ids:
            if line.product_id.tracking == 'none':
                if len(line.move_from_id.move_line_ids) != 0:
                    for m_line in line.move_from_id.move_line_ids:
                        if m_line.qty_done == 0:
                            m_line.qty_done = m_line.product_uom_qty
            else:
                for item in line.lot_lines:
                    item.location_id = self.location_id.id
                    item.dest_location_id = self.dest_location_id.id
                    if all([x.lot_id != False and x.qty_done != 0 for x in line.move_from_id.move_line_ids]) or not len(line.move_from_id.move_line_ids):
                        stock_move_out_line_vals = {
                            'product_id': line.product_id.id,
                            'origin': self.name,
                            'product_uom_id': line.product_uom.id,
                            'qty_done': item.qty_done,
                            'location_id': self.location_id.id,
                            'location_dest_id': self.dest_location_id.id,
                            'name': line.product_id.name,
                            'move_id': line.move_from_id.id,
                            'state': 'draft',
                            'picking_id': self.picking_from_id.id,
                            'lot_id': item.lot_id.id,
                            'lot_name': item.lot_id.name,
                        }
                        self.env['stock.move.line'].create(stock_move_out_line_vals)
                    else:
                        for move_line in line.move_from_id.move_line_ids:
                            if move_line.qty_done == 0 or not move_line.lot_id:
                                move_line.qty_done = item.qty_done
                                move_line.lot_id = item.lot_id.id
                                move_line.lot_name = item.lot_id.name
                                break
        for line in self.transfer_line_ids:
            if line.product_id.tracking != 'none':
                if line.qty_done < line.qty:
                    raise except_orm(_('Thông báo'), _(
                        'Bạn chưa nhập đủ chi tiết số lô/serial cho sản phẩm "%s". Vui lòng cập nhật thêm để hoàn thành đơn!' % line.product_id.name))
                elif line.qty_done > line.qty:
                    raise except_orm(_('Thông báo'), _(
                        'Bạn đã nhập chi tiết số lô/serial lớn hơn số lượng dịch chuyển ban đầu. Chi tiết sản phẩm "%s".' % line.product_id.name))
        self.picking_from_id.button_validate()
        if not self.picking_from_id.state == 'done':
            raise except_orm(_('Thông báo'), _('Gặp vấn đề ở đơn dịch chuyển kho. Vui lòng liên hệ quản trị viên'))
        if self.warehouse_id.id == self.dest_warehouse_id.id:
            self.state = 'done'
        else:
            self._create_account_move()
            self.state = 'transfer'

    @api.multi
    def action_receive(self):
        if self.state != 'transfer':
            return True
        picking_type_to_id = self.dest_warehouse_id.int_type_id
        picking_id = self._create_picking(picking_type_to_id.id, self.dest_location_id.id, self.dest_warehouse_id.x_wh_transfer_loc_id.id,
                                          self.dest_branch_id.id, False)
        if picking_id.id == False:
            raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
        self.update({'picking_to_id': picking_id.id, 'date_receive': fields.Datetime.now()})
        picking_id.action_confirm()
        if self.picking_to_id.state == 'done':
            self.state = self.picking_to_id.state
        else:
            self.picking_to_id.action_assign()
            for line in self.transfer_line_ids:
                if line.product_id.tracking == 'none':
                    if len(line.move_to_id.move_line_ids) != 0:
                        for m_line in line.move_to_id.move_line_ids:
                            if m_line.qty_done == 0:
                                m_line.qty_done = m_line.product_uom_qty
                else:
                    for item in line.lot_lines:
                        item.location_id = self.location_id.id
                        item.dest_location_id = self.dest_location_id.id
                        if all([x.lot_id != False and x.qty_done != 0 for x in line.move_to_id.move_line_ids]) or not len(line.move_to_id.move_line_ids):
                            stock_move_out_line_vals = {
                                'product_id': line.product_id.id,
                                'origin': self.name,
                                'product_uom_id': line.product_uom.id,
                                'qty_done': item.qty_done,
                                'location_id': self.location_id.id,
                                'location_dest_id': self.dest_location_id.id,
                                'name': line.product_id.name,
                                'move_id': line.move_to_id.id,
                                'state': 'draft',
                                'picking_id': picking_id.id,
                                'lot_id': item.lot_id.id,
                                'lot_name': item.lot_id.name,
                            }
                            self.env['stock.move.line'].create(stock_move_out_line_vals)
                        else:
                            for move_line in line.move_to_id.move_line_ids:
                                if move_line.qty_done == 0 or not move_line.lot_id:
                                    move_line.qty_done = item.qty_done
                                    move_line.lot_id = item.lot_id.id
                                    move_line.lot_name = item.lot_id.name
                                    break
            self.picking_to_id.button_validate()
            self._create_dest_account_move()
            self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer') or _('New')
        return super(StockTransfer, self).create(vals)

    @api.multi
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise UserError(_('Thông báo'), ('Bạn chỉ có thể xóa khi ở trạng thái Nháp'))
        return super(StockTransfer, self).unlink()

    @api.multi
    def action_back(self):
        if self.picking_from_id:
            self.picking_from_id.action_cancel()
            self.picking_from_id.unlink()
        self.state = 'draft'

    @api.multi
    def action_cancel(self):
        if self.picking_from_id:
            self.picking_from_id.action_cancel()
        self.state = 'cancel'

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    @api.multi
    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 3
            lines = []
            while index < sheet.nrows:
                product_code = sheet.cell(index, 1).value
                product_id = False
                uom_id = False
                lot_id = False
                lot_line = []
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)],limit=1)
                if product_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                product_id = product_obj.id
                uom_id = product_obj.product_tmpl_id.uom_id.id
                qty = sheet.cell(index, 4).value
                lot_name = sheet.cell(index, 5).value.strip().upper()
                if lot_name:
                    life_date = sheet.cell(index, 6).value
                    lot_id = self.env['stock.production.lot'].search([('name', 'like', lot_name),('product_id','=',product_id)],limit=1)
                    if lot_id.id == False:
                        lot_id = self.env['stock.production.lot'].create({
                            'name': lot_name,
                            'product_id': product_id,
                            'life_date': life_date,
                            'product_uom_id': uom_id})
                    line_argv = {
                        'location_id': self.location_id.id,
                        'dest_location_id': self.dest_location_id.id,
                        'uom_id': uom_id,
                        'lot_id':lot_id.id,
                        'lot_name':lot_name,
                        'life_date':life_date,
                        'qty_done': qty,
                        'product_id': product_id,
                    }
                    lot_line.append(line_argv)
                note = sheet.cell(index, 7).value
                if all([x['product_id'] != product_id for x in lines]) or len(lines) == 0:
                    argvs = {
                        'product_id': product_id,
                        'product_uom': uom_id,
                        'qty': qty,
                        'note': note,
                        'lot_lines':lot_line
                    }
                    lines.append(argvs)
                else:
                    for dict in lines:
                        if dict['product_id'] == product_id:
                            dict['qty'] += qty
                            for l in lot_line:
                                dict['lot_lines'].append(l)
                index = index + 1
            self.transfer_line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_transfer/static/template/import_izi_stock_transfer.xlsx',
            "target": "_parent",
        }


    @api.multi
    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_stock_transfer.report_template_stock_picking_internal_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }
