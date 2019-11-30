# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date

class BankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    x_lot_ids = fields.Many2many('stock.production.lot',string="Lot & Serial")
