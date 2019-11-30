# -*- coding: utf-8 -*-
from odoo import models, fields, _, time, api


class PosorderInherit(models.Model):
    _inherit = 'pos.order'

    # added by HoiHD
    def get_employee_make_service(self):
        employee = []
        pos_use_service_id = self.env['pos.use.service'].search([('pos_order_id', '=', self.id)])
        if pos_use_service_id:
            pos_use_service_line_ids = self.env['pos.use.service.line'].search([('use_service_id', '=', pos_use_service_id.id)])
            if len(pos_use_service_line_ids) != 0:
                for line in pos_use_service_line_ids:
                    if len(line.employee_ids) != 0:
                        for item in line.employee_ids:
                            if item.display_name not in employee:
                                employee.append(item.display_name)
        return employee

    # added by HoiHD
    # lay ra cac phuong thuc thanh toan va tien tru ghi no
    # def get_payment_method_and_money_without_debit(self):
    #     payment_method = {}
    #     for line in self:
    #         if line.statement_ids:
    #             for item in line.statement_ids:
    #                 if item.journal_id.type != 'debit':
    #                     if item.journal_id.x_through_intermediary is True:
    #                         partner_name = str(item.journal_id.name) + "(" + str(item.x_intermediary_partner_id.name) + ")"
    #                         if partner_name in payment_method.keys():
    #                             payment_method[partner_name] += item.amount
    #                         else:
    #                             payment_method.update({partner_name: item.amount})
    #                     else:
    #                         partner_name_1 = str(item.journal_id.name)
    #                         if partner_name_1 in payment_method.keys():
    #                             payment_method[partner_name_1] += item.amount
    #                         else:
    #                             payment_method.update({partner_name_1: item.amount})
    #     return payment_method

    # added by HoiHD
    # lay ra cac phuong thuc thanh toan ghi no
    # def get_payment_method_with_debit(self):
    #     payment_method_debit = {}
    #     for line in self:
    #         if line.statement_ids:
    #             amount = 0
    #             for item in line.statement_ids:
    #                 if item.journal_id.type == 'debit':
    #                     amount += item.amount
    #                     payment_method_debit.update({str(item.journal_id.name): amount})
    #     return payment_method_debit

    def _compute_sum_discount(self,check):
        total_discount= 0
        for item in self.lines:
            if item.discount != 100:
                total_discount += item.qty * item.price_unit * item.discount / 100
        return total_discount

    def _compute_sum_money(self):
        total_money = 0
        for record in self:
            for item in record.lines:
                if item.discount != 100 and item.price_subtotal != 0:
                    total_money += item.qty * item.price_unit
        return total_money

    @api.multi
    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_pos_report.pos_report_bill/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }
