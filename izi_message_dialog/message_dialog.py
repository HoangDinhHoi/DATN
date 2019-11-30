# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/3/2019

from .message_dialog_config import MessageDialogConfig


class MessageDialog(object):

    @staticmethod
    def show_info_dialog(env, title, message, size):
        message_dialog = env['message.dialog']
        return message_dialog.show_dialog(title, message, MessageDialogConfig.MessageDialogType.INFO, size)

    @staticmethod
    def show_warning_dialog(env, title, message, size):
        message_dialog = env['message.dialog']
        return message_dialog.show_dialog(title, message, MessageDialogConfig.MessageDialogType.WARNING, size)

    @staticmethod
    def show_error_dialog(env, title, message, size):
        message_dialog = env['message.dialog']
        return message_dialog.show_dialog(title, message, MessageDialogConfig.MessageDialogType.ERROR, size)
