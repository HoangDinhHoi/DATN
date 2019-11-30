# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/14/2019

from odoo import api, fields, models, _

from addons_custom.izi_message_dialog.message_dialog_config import MessageDialogConfig


class MessageDialog(models.TransientModel):
    _name = 'message.dialog'
    _description = 'Message dialog'

    title = fields.Char(string='Title')
    message = fields.Html(string='Message')

    @api.multi
    def show_dialog(self, title, message, type=MessageDialogConfig.MessageDialogType.INFO,
                    size=MessageDialogConfig.MessageDialogSize.MEDIUM, show_close_button=False):
        dialog = self.create({'title': title,
                              'message': message})
        return dialog.__show(type=type, size=size, show_close_button=show_close_button)

    def __show(self, type=MessageDialogConfig.MessageDialogType.INFO, size=MessageDialogConfig.MessageDialogSize.MEDIUM,
               show_close_button=False):
        view = self.env.ref('izi_message_dialog.message_dialog')
        ctx = self._context.copy()
        ctx.update({'dialog_size': size,
                    'izi_dialog': True,
                    'izi_type': type,
                    'izi_show_close_button': show_close_button})
        return {
            'name': _(self.title),
            'type': 'ir.actions.act_window',
            'res_model': 'message.dialog',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': ctx,
            'flags': {'form': {'action_buttons': False}}
        }
