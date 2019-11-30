# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning as UserError

SUPERUSER_ID = 1

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def open_frontend_cb(self):
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

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']
        new = super(PosSession, self).create(vals)
        if not new.config_id: except_orm('Thông báo', 'Chưa chọn điểm bán hàng khi tạo phiên!')
        if not new.config_id.x_pos_session_sequence_id: except_orm('Thông báo', 'Điểm bán hàng %s chưa cấu hình quy tăc sinh mã phiên. Vui lòng cấu hình trước khi tạo phiên mới!' % (new.config_id.name, ))

        new.name = str(SequenceObj.next_by_code(new.config_id.x_pos_session_sequence_id.code))

        return new
    # Ghi đề hàm của core để cho phép thanh toán bằng các hình thức khác bank và card
    @api.multi
    def action_pos_session_close(self):
        # Close CashBox
        for session in self:
            company_id = session.config_id.company_id.id
            ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
            for st in session.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.user_has_groups("point_of_sale.group_pos_manager"):
                        raise UserError(_(
                            "Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (
                                            st.difference, st.journal_id.amount_authorized_diff))
                # if (st.journal_id.type not in ['bank', 'cash']):
                #     raise UserError(_("The journal type for your payment method should be bank or cash."))
                st.with_context(ctx).sudo().button_confirm_bank()
        self.with_context(ctx)._confirm_orders()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }