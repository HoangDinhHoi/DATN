# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import except_orm


class PosUseServiceReport(models.Model):
    _inherit = 'pos.use.service'

    # In Su dung dich vu added by HoiHD
    @api.multi
    def action_print(self):
        if self.type == 'card':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_pos_use_service.report_template_pos_use_service_retail_service_view/%s' % (
                    self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_pos_report.pos_report_bill/%s' % (self.pos_order_id.id),
                'target': 'new',
                'res_id': self.id,
            }

    # lay ra nhan vien lam added by HoiHD
    def get_employee_do_service(self):
        line_ids = self.env['pos.use.service.line'].search([('use_service_id', '=', self.id)])
        employees = []
        if line_ids:
            for line in line_ids:
                for item in line.employee_ids:
                    employees.append(item.display_name)
        return list(set(employees))

    # lay ra tong tien truoc chiet khau
    def get_amount_total_without_discount(self):
        amount_total_without_discount = 0.0
        for line in self:
            for item in line.use_service_ids:
                if item.discount != 100:
                    amount_total_without_discount += item.qty * item.price_unit
        return amount_total_without_discount

    # lay ra tong chiet khau bang tien
    def get_discount_by_money(self):
        discount_by_money = 0
        for line in self:
            for item in line.use_service_ids:
                if item.discount and item.discount != 100:
                    discount_by_money += item.qty * item.price_unit * item.discount / 100
        return discount_by_money

    # lay ra cac phuong thuc thanh toan va tien tru ghi no
    # def get_payment_method_and_money_without_debit(self):
    #     payment_method = {}
    #     for line in self:
    #         if line.payment_ids:
    #             for item in line.payment_ids:
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

    # lay ra cac phuong thuc thanh toan ghi no
    def get_payment_method_with_debit(self):
        payment_method_debit = {}
        for line in self:
            if line.payment_ids:
                amount = 0
                for item in line.payment_ids:
                    if item.journal_id.type == 'debit':
                        amount += item.amount
                        payment_method_debit.update({str(item.journal_id.name): amount})
        return payment_method_debit



