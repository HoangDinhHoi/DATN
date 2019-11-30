# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    x_bank_card_id = fields.Many2one('pos.bank.card', 'Bank card')
    x_check_payment_bank = fields.Boolean(default=False)

    @api.onchange('journal_id')
    def _onchange_check_payment_bank(self):
        list = []
        if self.journal_id:
            if self.journal_id.type == 'bank':
                self.x_check_payment_bank = True
                bank_card_obj = self.env['pos.bank.card'].search(
                    [('journal_id', '=', self.journal_id.id), ('active', '=', True), ('company_id', '=', self.journal_id.company_id.id)])
                for item in bank_card_obj:
                    list.append(item.id)
            else:
                self.x_bank_card_id = False
                self.x_check_payment_bank = False
        return {
            'domain': {'x_bank_card_id': [('id', 'in', list)]}
        }

    @api.multi
    def check(self):
        context = dict(self._context or {})
        context['x_bank_card_id'] = False
        if self.x_bank_card_id:
            context['x_bank_card_id'] = self.x_bank_card_id.id
        return super(PosMakePayment, self.with_context(context)).check()

