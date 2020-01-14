# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class PosUseService(models.Model):
    _inherit = 'pos.use.service'

    signature = fields.Binary("Signature", attachment=True, store=True)
    customer_confirm = fields.Boolean(related='pos_session_id.config_id.module_izi_pos_customer_confirm',
                                      string="Customer Confirm")
    # custmer_confirm_id = fields.Many2one('pos.customer.confirm', "Customer Confirm")

    @api.multi
    def action_done(self):
        if self.pos_session_id.config_id.module_izi_pos_customer_confirm is False:
            return self._action_done()
        else:
            view = self.env.ref('izi_pos_customer_confirm.izi_pos_use_service_confirm_form')
            return {
                'name': _('Sign Customer?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.use.service',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }

    @api.multi
    def action_customer_signature(self):
        self.write({
            'signature': self.signature
        })
        if self.pos_order_id:
            self.pos_order_id.write({
                'x_signature': self.signature
            })
        return self._action_done()


class PosUseServiceLine(models.Model):
    _inherit = 'pos.use.service.line'

    customer_rate = fields.Selection([(0, 'Normal'), (1, 'Good'), (2, "Excellent")], default=2)
    # custmer_confirm_id = fields.Many2one('pos.customer.confirm', "Customer Confirm")
