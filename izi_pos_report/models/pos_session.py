# -*- coding: utf-8 -*-
from odoo import models, fields, _, time, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_print_bill(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_pos_report.pos_report_session/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def action_print_case(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_pos_report.pos_report_case_session/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def funtion_sum(self):
        for record in self:
            total_sum = 0
            for line in record.statement_ids:
                total_sum += line.balance_end
        return total_sum

    def funtion_sum_casesession(self):
        for record in self:
            total_sum_case = 0
            for line in record.statement_ids:
                total_sum_case += line.balance_end_real
        return total_sum_case

    def sum_order(self):
        name = self.name
        order = self.env['pos.order'].search([('session_id', '=', self.id)])
        total_sum_order = len(order)
        return total_sum_order

    def product_in_order(self):
        order_lines = self.env['pos.order'].search(
            [('session_id', '=', self.id), ('state', '!=', 'cancel' and 'draft')])
        list_product = []
        list_service=[]
        for item in order_lines:
            for line in item.lines:
               if line.product_id.type != 'service':
                   if len(list_product) == 0:
                       dict = {
                           'code': line.product_id.default_code,
                           'product_id': line.product_id.name,
                           'qty': line.qty,
                           'price_subtotal_incl': line.price_subtotal_incl,
                       }
                       list_product.append(dict)
                   else:
                       if all([line.product_id.default_code != list['code'] for list in list_product]):
                           dict2 = {
                               'code': line.product_id.default_code,
                               'product_id': line.product_id.name,
                               'qty': line.qty,
                               'price_subtotal_incl': line.price_subtotal_incl,
                           }
                           list_product.append(dict2)
                       else:
                           for list in list_product:
                               if list['code'] == line.product_id.default_code:
                                   list['qty'] += line.qty
                                   list['price_subtotal_incl'] += line.price_subtotal_incl
        return list_product

    def service_card_in_order(self):
        order_lines = self.env['pos.order'].search(
            [('session_id', '=', self.id), ('state', '!=', 'cancel' and 'draft')])
        list_service = []
        for item in order_lines:
            for line in item.lines:
               if line.product_id.type == 'service':
                   if len(list_service) == 0:
                       dict = {
                           'code': line.product_id.default_code,
                           'product_id': line.product_id.name,
                           'qty': line.qty,
                           'price_subtotal_incl': line.price_subtotal_incl,
                       }
                       list_service.append(dict)
                   else:
                       if all([line.product_id.default_code != list['code'] for list in list_service]):
                           dict2 = {
                               'code': line.product_id.default_code,
                               'product_id': line.product_id.name,
                               'qty': line.qty,
                               'price_subtotal_incl': line.price_subtotal_incl,
                           }
                           list_service.append(dict2)
                       else:
                           for list in list_service:
                               if list['code'] == line.product_id.default_code:
                                   list['qty'] += line.qty
                                   list['price_subtotal_incl'] += line.price_subtotal_incl
        return list_service
