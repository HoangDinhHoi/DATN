# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm


class PosBankCard(models.Model):
    _name = 'pos.bank.card'

    name = fields.Char('Name')
    code = fields.Char('Code')
    description = fields.Text('Description')
    journal_id = fields.Many2one('account.journal', 'Payment journal')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('pos.bank.card.line', 'bank_id', string='Line')

    @api.model
    def create(self, vals):
        if 'code' in vals:
            my_code = self.env['pos.bank.card'].search([('code', '=', vals.get('code').strip().upper())])
            if my_code:
                raise except_orm('Thông báo', 'Mã bạn nhập đã tồn tại.')
            vals['code'] = vals.get('code').strip().upper()
        return super(PosBankCard, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('code') and vals.get('code') != '':
            my_code = self.env['pos.bank.card'].search([('code', '=', vals.get('code').strip().upper())])
            if my_code:
                raise except_orm('Thông báo', 'Mã bạn nhập đã tồn tại.')
            vals['code'] = vals.get('code').strip().upper()
        return super(PosBankCard, self).write(vals)


class PosBankCardLine(models.Model):
    _name = 'pos.bank.card.line'

    account_id = fields.Many2one('account.account', 'Account cost')
    cost_rate = fields.Float('Cost Rate')
    description = fields.Text('Description')
    bank_id = fields.Many2one('pos.bank.card',string='Bank')


