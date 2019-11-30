# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/5/2019

from odoo import api, fields, models, _
from odoo.exceptions import except_orm

from addons_custom.izi_message_dialog.message_dialog_config import MessageDialogConfig


class SaleOrderMakePosOrder(models.TransientModel):
    _name = 'sale.order.make.pos.order'
    _inherit = ['message.dialog']

    pos_config_id = fields.Many2one('pos.config', string='Pos config')
    pos_session_id = fields.Many2one('pos.session', string='Pos session')

    @api.onchange('pos_config_id')
    def _onchange_pos_config_id(self):
        if self.pos_config_id:
            session = self.env['pos.session'].search([('config_id', '=', self.pos_config_id.id),
                                                      ('state', '=', 'opened')], limit=1)
            self.pos_session_id = session.id if session else False

    @api.multi
    def create_pos_order(self):
        if not self.pos_session_id:
            raise except_orm(_('Warning'), _('Request to create a session before create pos order.'))
        pos = self.move_to_pos()
        return self.__get_pos_view(pos)

    def __get_pos_view(self, pos):
        view_id = self.env.ref('point_of_sale.view_pos_pos_form').id
        return {
            'name': pos.name,
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': pos.id,
            'context': dict(self._context),
        }

    def move_to_pos(self):
        sale_order = self.env['sale.order'].browse(self._context.get('sale_order_id'))
        if not sale_order:
            raise except_orm(_('Error'), _('Sale order not exists'))

        pos = self.__create_pos_order(sale_order)
        sale_order.state = 'moved_to_pos'
        return pos

    def __create_pos_order(self, sale_order):
        pos_session = self.env['pos.session'].browse(self.pos_session_id.id)

        lines = []
        for line in sale_order.order_line:
            lines.append((0, 0, {
                'company_id': line.company_id.id,
                'name': line.name,
                'product_id': line.product_id.id,
                'qty': line.product_uom_qty,
                'discount': line.discount,
                'price': line.price_unit,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_subtotal_incl': line.price_total
            }))

        if len(lines) < 1:
            raise except_orm('Cảnh báo', 'Đơn hàng chưa có sản phẩm,\n'
                                         'vui lòng cập nhật lại để có thể thực hiện tác vụ này.')

        pos_order_vals = {
            'amount_tax': sale_order.amount_tax,
            'amount_total': sale_order.amount_total,
            'partner_id': sale_order.partner_id.id,
            'date_order': sale_order.date_order,
            'x_rank_id': sale_order.partner_id.x_rank_id.id,
            'pricelist_id': sale_order.pricelist_id.id,
            'user_id': pos_session.user_id.id,
            'x_team_id': pos_session.user_id.sale_team_id.id,
            'company_id': sale_order.company_id.id,
            'session_id': pos_session.id,
            'branch_id': sale_order.branch_id.id,
            'pos_reference': sale_order.name,
            'note': sale_order.note,
            'sale_order_id': sale_order.id,
            'lines': lines
        }

        pos = self.env['pos.order'].create(pos_order_vals)
        return pos

    def get_dialog(self):
        view_id = self.env.ref('izi_sale_order.sale_order_make_pos_order').id
        ctx = self._context.copy()
        ctx.update({
            'izi_type': MessageDialogConfig.MessageDialogType.INFO,
            'dialog_size': MessageDialogConfig.MessageDialogSize.MEDIUM
        })
        return {
            'name': 'Choose session to create pos order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.make.pos.order',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }
