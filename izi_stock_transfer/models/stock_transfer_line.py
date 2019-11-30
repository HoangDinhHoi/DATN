# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, except_orm
from odoo.exceptions import UserError


class StockTransferLine(models.Model):
    _name = 'stock.transfer.line'

    product_id = fields.Many2one('product.product', 'Product', domain=[('type', 'in', ['product', 'consu'])])
    name = fields.Char('Product name')
    qty = fields.Float('Qty')
    qty_available = fields.Char('Status')
    qty_done = fields.Float('Qty done', compute='_compute_qty_done')
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    stock_transfer_id = fields.Many2one('stock.transfer', 'Stock transfer')
    move_from_id = fields.Many2one('stock.move', 'Stock Move from')
    move_to_id = fields.Many2one('stock.move', 'Stock Move to')
    note = fields.Text('Note')
    show_details_visible = fields.Boolean('Details Visible', compute='_compute_show_details_visible')
    lot_lines = fields.One2many('stock.transfer.lot.line', 'transfer_line_id', string='Transfer lot')

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
                if item.stock_transfer_id.state == 'done':
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

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id.with_context(lang=self.env.user.lang)
        self.name = product.partner_ref
        self.product_uom = product.uom_id.id
        return {'domain': {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}}

    def _create_stock_moves(self, picking, transfer):
        moves = self.env['stock.move']
        for line in self:
            vals = line._prepare_stock_moves(picking,transfer)
            move_id = moves.create(vals)
            if transfer:
                line.move_from_id = move_id.id
            else:
                line.move_to_id = move_id.id


    @api.multi
    def _prepare_stock_moves(self, picking, transfer=True):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.qty,
            'date': self.stock_transfer_id.scheduled_date if transfer else fields.Datetime.now(),
            'date_expected': self.stock_transfer_id.scheduled_date if transfer else fields.Datetime.now(),
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'branch_id': picking.branch_id.id,
            'state': 'draft',
            'company_id': self.stock_transfer_id.company_id.id,
            'picking_type_id': picking.picking_type_id.id,
            'origin': self.stock_transfer_id.name,
            'route_ids': (picking.picking_type_id.warehouse_id and [
                (6, 0, [x.id for x in picking.picking_type_id.warehouse_id.route_ids])] or []),
            'warehouse_id': picking.picking_type_id.warehouse_id.id,
        }
        res.append(template)
        return res

    @api.multi
    def action_show_details(self):
        if not len(self.lot_lines):
            if self.product_id.tracking == 'lot':
                self.env['stock.transfer.lot.line'].create({
                    'transfer_line_id': self.id,
                    'location_id': self.stock_transfer_id.location_id.id,
                    'dest_location_id': self.stock_transfer_id.dest_location_id.id,
                    'uom_id': self.product_uom.id,
                    'qty_done': self.qty,
                    'product_id': self.product_id.id,
                })
            elif self.product_id.tracking == 'serial':
                for tmp in range(0, int(self.qty)):
                    self.env['stock.transfer.lot.line'].create({
                        'transfer_line_id': self.id,
                        'location_id': self.stock_transfer_id.location_id.id,
                        'dest_location_id': self.stock_transfer_id.dest_location_id.id,
                        'uom_id': self.product_uom.id,
                        'qty_done': 1,
                        'product_id': self.product_id.id,
                    })
        ctx = self.env.context.copy()
        ctx.update({'loca_id': self.stock_transfer_id.location_id.id, 'loca_dest_id': self.stock_transfer_id.dest_location_id.id})
        if self.stock_transfer_id.state in ('done','transfer'):
            ctx.update({'done': True})
        view = self.env.ref('izi_stock_transfer.izi_stock_transfer_lot_line_tree_view')
        return {
            'name': _('Add lot'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.transfer.line',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
        }


class StockTransferLotLine(models.Model):
    _name = 'stock.transfer.lot.line'

    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'From')
    dest_location_id = fields.Many2one('stock.location', 'To')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial Number')
    lot_name = fields.Char('Lot/Serial Number Name')
    life_date = fields.Date(string='Life Date', compute='_compute_life_date')
    qty_done = fields.Float('Qty Done')
    uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True)
    transfer_line_id = fields.Many2one('stock.transfer.line', 'Stock transfer line')

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
