# -*- coding: utf-8 -*-

from odoo import api, fields, models

from addons_custom.izi_message_dialog.message_dialog_config import MessageDialogConfig


class ConfirmDialog(models.TransientModel):
    _name = 'confirm.dialog'
    _inherit = ['message.dialog']

    message = fields.Text(string='Message')

    def get_no_sale_confirm_dialog(self):
        view_id = self.env.ref('izi_crm_booking.meeting_no_sale_confirm_dialog').id
        ctx = self._context.copy()
        ctx.update({
            'dialog_size': MessageDialogConfig.MessageDialogSize.SMALL,
            'izi_dialog': True,
            'izi_type': MessageDialogConfig.MessageDialogType.ERROR
        })
        return {
            'name': 'Would you like to create another meeting?',
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.dialog',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_yes(self):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        ctx = self._context.copy()
        ctx.update({'default_customer_id': ctx.get('customer_id'),
                    'default_type': 'meeting'})
        return {
            'name': 'Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    @api.multi
    def action_no(self):
        view_id = self.env.ref('izi_crm_booking.message_form_dialog').id
        ctx = self._context.copy()
        ctx.update({
            'dialog_size': MessageDialogConfig.MessageDialogSize.MEDIUM,
            'izi_dialog': True,
            'izi_type': MessageDialogConfig.MessageDialogType.ERROR
        })
        return {
            'name': 'Why not create a new meeting?',
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.dialog',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_save_region(self):
        meeting_id = self._context.get('meeting_id')
        meeting = self.env['service.booking'].browse(meeting_id)
        meeting.write({'reason_no_sale': self.message,
                       'state': 'no_sale'})
