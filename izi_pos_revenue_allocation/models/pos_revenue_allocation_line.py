# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosRevenueAllocationLine(models.Model):
    _name = 'pos.revenue.allocation.line'

    employee_id = fields.Many2one('hr.employee', "Employee")
    amount_product = fields.Float("Amount Product")
    amount_service = fields.Float("Amount Service")
    amount_keep = fields.Float("Amount Keep")
    amount_product_percent = fields.Float("Amount Product Percent")
    amount_service_percent = fields.Float("Amount Service Percent")
    amount_keep_percent = fields.Float("Amount Keep Percent")
    revenue_allocation_id = fields.Many2one('pos.revenue.allocation', "Revenue Allocation")
    note = fields.Text(string='Note')

    @api.onchange('amount_product_percent', 'amount_service_percent', 'amount_keep_percent', 'revenue_allocation_id')
    def _onchange_percent(self):
        for order in self:
            order.amount_product = order.revenue_allocation_id.amount_total * order.amount_product_percent / 100
            order.amount_service = order.revenue_allocation_id.amount_total * order.amount_service_percent / 100
            order.amount_keep = order.revenue_allocation_id.amount_total * order.amount_keep_percent / 100

    @api.onchange('amount_product', 'amount_service', 'amount_keep', 'revenue_allocation_id')
    def _onchange_amount(self):
        for order in self:
            if order.revenue_allocation_id.amount_total == 0:
                continue
            order.amount_product_percent = order.amount_product / order.revenue_allocation_id.amount_total * 100
            order.amount_service_percent = order.amount_service / order.revenue_allocation_id.amount_total * 100
            order.amount_keep_percent = order.amount_keep / order.revenue_allocation_id.amount_total * 100
