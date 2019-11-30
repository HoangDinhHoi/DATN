# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/8/2019

from odoo import api, fields, models, _

STATE_SELECTOR = [('new', 'New'), ('assigned', 'Assigned'), ('won', 'Won'), ('dead', 'Dead'),
                  ('contact', 'Contact'), ('no_pick_up', 'No pick up'), ('wrong_number', 'Wrong number'),
                  ('booking', 'Booking'), ('meeting', 'Meeting'), ('sale_order', 'Sale order')]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ref_sale_order_id = fields.Many2one('sale.order', string='Sale order')
    state = fields.Selection(STATE_SELECTOR, default="new", string="State", track_visibility='onchange')

    @api.multi
    def action_sale_order(self):
        view_id = self.env.ref('sale.view_order_form').id
        sale_order = self.create_sale_order()
        return {
            'name': self.name + ' - ' + 'order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'res_id': sale_order.id,
            'context': dict(self._context),
        }

    def create_sale_order(self):
        if not self.contact_id.partner_id:
            ctx = {
                'lang': self._context.get('lang'),
                'tz': self._context.get('tz'),
                'uid': self._context.get('uid')
            }
            self.contact_id.with_context({}, **ctx).create_partner()
        order_line = []
        for line in self.product_quotation_ids:
            price_unit = self.__get_product_price_unit(self.contact_id.partner_id, line.product_id)
            order_line.append((0, 0, {'product_id': line.product_id.id,
                                      'name': line.product_id.name,
                                      'price_unit': price_unit,
                                      'product_uom': line.product_id.uom_id.id,
                                      'product_uom_qty': line.qty}))

        vals = {'type': 'retail',
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'branch_id': self.team_id.x_branch_id.id,
                'date_order': fields.Datetime.now(),
                'partner_id': self.contact_id.partner_id.id,
                'order_line': order_line}

        sale_order = self.env['sale.order'].create(vals)
        self.write({'state': 'sale_order',
                    'ref_sale_order_id': sale_order.id})
        return sale_order

    @staticmethod
    def __get_product_price_unit(customer, product):
        discount = customer.x_rank_id.discount_service if product.type == 'service' \
            else customer.x_rank_id.discount_product
        price = customer.property_product_pricelist.get_product_price(product, 1, customer)
        return price - ((price * discount) / 100)
