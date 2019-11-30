# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PosBankSession(models.Model):
    _inherit = 'pos.session'

    # tao but toan phi quet the ngan hang
    @api.multi
    def action_pos_session_close(self):
        print('Tiendz')
        order_ids = self.env['pos.order'].search([('session_id','=',self.id)])
        for order_id in order_ids:
            for line in order_id.statement_ids:
                if line.x_bank_card_id and line.journal_id.type == 'bank':
                    self._get_move_bank_card(line)
        return super(PosBankSession,self).action_pos_session_close()

    def _get_move_bank_card(self, statement_id):
        move_lines = []
        amount = statement_id.x_bank_card_id.cost_rate /100 * statement_id.amount
        if amount > 0:
            credit_move_vals = {
                'name': statement_id.name,
                'account_id': statement_id.journal_id.default_credit_account_id.id,
                'credit': amount,
                'debit': 0.0,
                'partner_id': statement_id.pos_statement_id.partner_id.id,
            }
            debit_move_vals = {
                'name': statement_id.name,
                'account_id': statement_id.x_bank_card_id.account_id.id,
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
                'account_id': statement_id.x_bank_card_id.account_id.id,
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
        }
        move_id = self.env['account.move'].create(vals_account)
        move_id.post()
        return True
