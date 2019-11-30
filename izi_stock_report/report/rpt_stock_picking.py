# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportStockPickingQweb(models.Model):
    _inherit = 'stock.picking'

    is_return_promissory_note = fields.Boolean(default=False, string='Check Return Promissory Note')
    ref_po = fields.Char(string='Reference Purchase Order')

    @api.multi
    def action_print_picking(self):
        if self.picking_type_id.code == 'incoming':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_stock_report.report_template_stock_picking_incoming_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.picking_type_id.code == 'outgoing':
            self.check_return_promissory_note()
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_stock_report.report_template_stock_picking_outgoing_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            return True

    def check_return_promissory_note(self):
        """
            __author__: HoiHD
            Hàm này được tạo ra vì không thể lấy dữ liệu từ bảng tạm purchase_order_stock_picking_rel
            do việc không thể trả hàng với số lượng âm tại đơn PO --> phải tạo tay một đơn trả hàng
            --> có một vài picking trả hàng sẽ không có group_id, và thông tin của đơn đó không có trong bảng tạm bên
            trên.
        :return: Kiểm tra xem có phải đơn trả hàng hay không và thêm tham chiếu đơn PO vào.
        """
        position = self.origin.find('/IN/')
        if position != -1:
            self.is_return_promissory_note = True
            in_picking = self.search([('name', '=', self.origin.split(' ')[-1])], limit=1)
            if in_picking:
                self.ref_po = in_picking.origin

