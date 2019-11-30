# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools import float_is_zero
from dateutil.relativedelta import relativedelta

class PosUseServiceTransient(models.TransientModel):
    _name = 'pos.use.service.compare.transient'

    use_service_id = fields.Many2one('pos.use.service', "Use service")

    @api.multi
    def action_compare(self):
        for item in self:
            item.use_service_id.compare = 'valid'
            if item.use_service_id.pos_order_id:
                item.use_service_id.pos_order_id.x_compare = 'valid'
            item.use_service_id.user_compare_id = self.env.uid

    @api.multi
    def action_compare_not_ok(self):
        for item in self:
            item.use_service_id.compare = 'invalid'
            if item.use_service_id.pos_order_id:
                item.use_service_id.pos_order_id.x_compare = 'invalid'
            item.use_service_id.user_compare_id = self.env.uid


