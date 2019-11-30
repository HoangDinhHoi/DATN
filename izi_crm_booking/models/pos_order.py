# -*- coding: utf-8 -*-

from odoo import api,models


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        res = super(PosOrder, self).create(vals)
        if res.sale_order_id and res.sale_order_id.service_booking_ids:
            res.sale_order_id.service_booking_ids[0].ref_order_id = res.id
        return res


