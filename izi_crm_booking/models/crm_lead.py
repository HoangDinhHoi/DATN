# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

STATE_SELECTOR = [('new', 'New'), ('assigned', 'Assigned'), ('won', 'Won'), ('dead', 'Dead'),
                  ('contact', 'Contact'), ('no_pick_up', 'No pick up'), ('wrong_number', 'Wrong number'),
                  ('booking', 'Booking'), ('meeting', 'Meeting')]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    state = fields.Selection(STATE_SELECTOR, default="new", string="State", track_visibility='onchange')

    @api.multi
    def action_booking(self):
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        if not self.contact_id.partner_id:
            ctx = {
                'lang': self._context.get('lang'),
                'tz': self._context.get('tz'),
                'uid': self._context.get('uid')
            }
            self.contact_id.with_context({}, **ctx).create_partner()

        products = self.__get_service_booking_products()

        ctx = {
            'lead_id': self.id,
            'default_type': type,
            'default_customer_id': self.contact_id.partner_id.id,
            'default_product_ids': products
        }
        return {
            'name': type[0].upper() + type[1:],
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    def __get_service_booking_products(self):
        if not self.product_quotation_ids:
            return []

        def get_total_amount(line):
            discount = self.partner_id.x_rank_id.discount_service if line.product_id.type == 'service' \
                else self.partner_id.x_rank_id.discount_product
            price = self.partner_id.property_product_pricelist.get_product_price(line.product_id, 1, self.partner_id)
            return (price - ((price * discount) / 100)) * line.qty

        if not self.contact_id.partner_id:
            self.contact_id.create_partner()

        products = [(0, 0, {'product_id': line.product_id.id,
                            'qty': line.qty,
                            'amount_total': get_total_amount(line)})
                    for line in self.product_quotation_ids]
        return products
