# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date

class BankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    x_bank_card_id = fields.Many2one('pos.bank.card','Bank card')
