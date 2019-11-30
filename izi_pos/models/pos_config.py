# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning as UserError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    # x_shop_id = fields.Many2one('res.partner', string='Shop')
    x_journal_loyal_ids = fields.Many2many('account.journal', 'journal_loyal_rel', string='Ghi nhận doanh thu',
                                         domain=[('journal_user', '=', True)],
                                         help='Các phương thức thanh toán được tính doanh thu')
    x_category_ids = fields.Many2many('pos.category', 'pos_config_pos_categ_rel', 'config_id', 'category_id', string="POS category")
    x_pos_session_sequence_id = fields.Many2one('ir.sequence', string="Pos session sequence")
    module_izi_pos_customer_confirm = fields.Boolean("Customer Confirm")


    @api.multi
    def open_ui(self):
        self.ensure_one()
        view = self.env.ref('point_of_sale.view_pos_pos_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_model': 'pos.order',
            'target': 'current',
        }

    # nút Resume => mở đơn bán pos
    @api.multi
    def open_ui(self):
        self.ensure_one()
        super(PosConfig, self).open_ui()

        view = self.env.ref('point_of_sale.view_pos_pos_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_model': 'pos.order',
            'target': 'current',
        }

    @api.multi
    def open_session_cb(self):
        self.ensure_one()
        return self._open_session(self.current_session_id.id)

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']

        new = super(PosConfig, self).create(vals)

        if not new.pos_branch_ids: raise except_orm('Thông báo', 'Chưa chọn chi nhánh cho điểm bán hàng %s' % (new.name, ))
        branch = new.pos_branch_ids[0]
        #tạo sequence session
        new.x_pos_session_sequence_id = SequenceObj.create({ 'name': 'POS session sequence [%s]%s' % (branch.code, branch.name, ), 'code': 'pos_session_%s_code' % (branch.code, ), 'prefix': 'POS/' + branch.code + '/%(y)s%(month)s/', 'padding': 4, 'company_id': new.company_id and new.company_id.id or False}).id
        #tạo sequence order
        new.sequence_id = SequenceObj.create({ 'name': 'POS order sequence [%s]%s' % (branch.code, branch.name, ), 'code': 'pos_order_%s_code' % (branch.code, ), 'prefix': branch.code + '/%(y)s%(month)s/', 'padding': 4, 'company_id': new.company_id and new.company_id.id or False}).id
        return new