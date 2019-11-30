# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date
from . import utils


class PosRevenueAllocation(models.Model):
    _name = 'pos.revenue.allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", track_visibility='onchange', copy=False)
    order_id = fields.Many2one('pos.order', "Order", track_visibility='onchange')
    amount_total = fields.Float("Amount Total", track_visibility='onchange')
    amount_allocated = fields.Float("Amount Allocated", track_visibility='onchange')
    remain_amount = fields.Float("Remain Amount")
    style_allocation = fields.Selection([('percent', "Percent"), ('money', "Money")], default='percent', track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('confirmed', "Confirmed"), ('editing', "Editing")], default='draft', track_visibility='onchange')
    revenue_allocation_ids = fields.One2many('pos.revenue.allocation.line', 'revenue_allocation_id', "Revenue Allocation")
    amount_product = fields.Float("Amount Product", track_visibility='onchange')
    amount_service = fields.Float("Amount Service", track_visibility='onchange')
    amount_keep = fields.Float("Amount Keep", track_visibility='onchange')
    date = fields.Date("Date", default=fields.Date.today())

    """
        Author: HoiHD
        Description:
            - Thêm mã tự tăng vào đơn phân bổ doanh thu theo quy tắc ALL + năm + tháng + 4 số tự tăng
        Date: 23/05/2019 on 9:29 AM
    """

    @api.model
    def create(self, vals):
        current_date = date.today().strftime('%y%m')
        code = 'ALL/' + current_date + '/'
        sequence_name = utils.get_sequence(self._cr, 1, code)
        new_code = self.env['pos.revenue.allocation'].search([('name', '=', sequence_name)])
        while len(new_code) > 0:
            sequence_name = utils.get_sequence(self._cr, 1, code)
            new_code = self.env['pos.revenue.allocation'].search([('name', '=', sequence_name)])
        vals['name'] = sequence_name
        return super(PosRevenueAllocation, self).create(vals)

    @api.multi
    def action_confirm(self):
        if self.state not in ('draft', 'editing'):
            raise except_orm("Thông báo!", ("Trạng thái đơn phân bổ đã thay đổi. Vui tải lại trang hoặc F5"))
        if self.order_id:
            if len(self.order_id.revenue_allocation_ids) > 1:
                raise except_orm('Thông báo!',
                                 ("Đơn hàng bạn chọn đã có đơn phân bổ doanh thu. Vui lòng tìm kiếm đơn phân bổ doanh thu hoặc đơn hàng để tiếp tục thao tác!"))
        if len(self.revenue_allocation_ids) == 0:
            raise except_orm('Cảnh báo!', ("Bạn chưa cập nhật chi tiết phân bổ doanh thu"))
        if self.remain_amount != 0:
            raise except_orm('Cảnh báo!', ("Số tiền chưa phân bổ khác 0. Bạn không thể đóng đơn phân bổ này!"))
        self.state = 'confirmed'

    @api.multi
    def action_edit(self):
        if self.state != 'confirmed':
            raise except_orm("Thông báo!", ("Trạng thái đơn phân bổ đã thay đổi. Vui tải lại trang hoặc F5"))
        self.state = 'editing'
        allo = self.env['pos.revenue.allocation'].search([('order_id', '=', self.order_id.id)], limit=1)
        if allo.id != False:
            view = self.env.ref('izi_pos_revenue_allocation.izi_pos_revenue_allocation_form')
            return {
                'name': _('Phân bổ doanh thu'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.revenue.allocation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': allo.id,
                'target': 'new',
                'context': self.env.context,
            }

    @api.onchange('order_id')
    def onchange_order_return(self):
        loyal_total = 0.0
        x_journal_loyal_ids = self.order_id.config_id.x_journal_loyal_ids.ids if self.order_id.config_id.x_journal_loyal_ids else False
        if x_journal_loyal_ids:
            for stt in self.order_id.statement_ids:
                if stt.journal_id.id in x_journal_loyal_ids:
                    if stt.amount != 0:
                        loyal_total += stt.amount
        self.amount_total = loyal_total

    @api.onchange('order_id')
    def onchange_order(self):
        ids = []
        crm_team_ids = self.env['crm.team'].search([('member_ids', '=', self.env.uid)])
        for line in crm_team_ids:
            config_id = self.env['pos.config'].search([('crm_team_id', '=', line.id)])
            if len(config_id) > 1:
                raise except_orm('Thông báo!', ("Một team đang thuộc 2 điểm bán hàng. Vui lòng kiểm tra lại cấu hình điểm bán hàng"))
            session_id = self.env['pos.session'].search([('config_id', '=', config_id.id), ('state', '=', 'opened')])
            order = self.env['pos.order'].search([('session_id', '=', session_id.id)])
            for line in order:
                revenue = self.env['pos.revenue.allocation'].search([('order_id', '=', line.id)])
                if revenue:
                    continue
                ids.append(line.id)
        return {
            'domain': {
                'order_id': [('id', 'in', ids)]
            }
        }

    @api.onchange('revenue_allocation_ids')
    def _onchange_revenue_allocation_ids(self):
        allocated_product = 0.0
        allocated_service = 0.0
        allocated_keep = 0.0
        for line in self.revenue_allocation_ids:
            allocated_product += line.amount_product
            allocated_service += line.amount_service
            allocated_keep += line.amount_keep
        self.amount_product = allocated_product
        self.amount_service = allocated_service
        self.amount_keep = allocated_keep
        self.remain_amount = (self.amount_total - allocated_product - allocated_service - allocated_keep)
