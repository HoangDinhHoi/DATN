# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta


class PosOrder(models.Model):
    _inherit = 'pos.order'

    # them data cho bien tạo account_bank_statement_line
    def _prepare_bank_statement_line_payment_values(self, data):
        args = super(PosOrder, self)._prepare_bank_statement_line_payment_values(data)
        if self._context.get('x_bank_card_id', False):
            args['x_bank_card_id'] = self._context.get('x_bank_card_id', False)
        return args


    @api.multi
    def action_confirm_order(self):
        for line in self.statement_ids:
            if line.x_bank_card_id and line.journal_id.type == 'bank':
                self._get_move_bank_card(line)
        return super(PosOrder,self).action_confirm_order()


    def _get_move_bank_card(self, statement_id):
        for item in statement_id.x_bank_card_id.line_ids:
            move_lines = []
            amount = item.cost_rate /100 * statement_id.amount
            if amount > 0:
                credit_move_vals = {
                    'name': statement_id.name,
                    'account_id': statement_id.journal_id.default_credit_account_id.id,
                    'credit': amount,
                    'debit': 0.0,
                    'partner_id': statement_id.pos_statement_id.partner_id.id,
                }
                debit_move_vals = {
                    'name': item.description,
                    'account_id': item.account_id.id,
                    'credit': 0.0,
                    'debit': amount,
                    'partner_id': statement_id.pos_statement_id.partner_id.id,
                }
                move_lines.append((0, 0, debit_move_vals))
                move_lines.append((0, 0, credit_move_vals))
            else:
                credit_move_vals = {
                    'name': statement_id.name,
                    'account_id': statement_id.journal_id.default_credit_account_id.id,
                    'credit': 0.0,
                    'debit': abs(amount),
                    'partner_id': statement_id.pos_statement_id.partner_id.id,
                }
                debit_move_vals = {
                    'name': statement_id.name,
                    'account_id': item.account_id.id,
                    'credit': abs(amount),
                    'debit': 0.0,
                    'partner_id': statement_id.pos_statement_id.partner_id.id,
                }
                move_lines.append((0, 0, debit_move_vals))
                move_lines.append((0, 0, credit_move_vals))
            vals_account = {
                'date': fields.Datetime.now(),
                'ref': statement_id.pos_statement_id.name,
                'journal_id': statement_id.journal_id.id,
                'line_ids': move_lines,
                'company_id': statement_id.pos_statement_id.company_id.id,
                'check_additional_account_move': True,  # thêm bởi HoiHD: Đây là bút toán phát sinh
            }
            move_id = self.env['account.move'].create(vals_account)
            move_id.post()
        return True