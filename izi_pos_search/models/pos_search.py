# -*- coding: utf-8 -*-
# __author__: HOIHD

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

WARNING = _('Warning!')


class IziPosSearch(models.TransientModel):
    _name = 'pos.search'

    name = fields.Char(default="Tra cứu thông tin")
    serial = fields.Char(string=_('Serial'))
    check_by_date = fields.Boolean(string=_('Check by Date'), default=False)
    from_date = fields.Date(string=_('From date'))
    to_date = fields.Date(string=_('To date'))

    coupon_ids = fields.One2many('coupon.transient', 'search_id',
                                 string=_('Coupon'))
    service_card_ids = fields.One2many('card.service.transient', 'search_id',
                                       string=_('Service Card'))
    detail_service_card_ids = fields.One2many('card.service.detail.transient', 'search_id',
                                              string=_('Service Card Detail'))
    history_service_card_ids = fields.One2many('card.service.history.transient', 'search_id',
                                               string=_('History Use Service Card'))
    # customer
    x_name = fields.Char(string=_('Partner Name'))
    x_partner_code = fields.Char(string=_('Partner Code'))
    x_partner_old_code = fields.Char(string='Partner Old Code')
    x_image = fields.Binary(string=_('Image'), attachment=True)
    x_rank_id = fields.Many2one('crm.customer.rank', string=_('Rank'))
    x_street = fields.Char(string=_('Street'))
    x_vat = fields.Char(string='VAT')
    x_phone = fields.Char(string=_('Phone'))
    x_email = fields.Char(string=_('Email'))
    x_deposit_amount_total = fields.Float(string=_('Amount Deposited'))
    x_balance_deposit = fields.Float(string=_('Deposit Balance'))

    check_coupon = fields.Boolean(string=_('Check Coupon'))
    check_service_card = fields.Boolean(string=_('Check Service Card'))
    x_company_id = fields.Many2one('res.company', string=_('Company'))

    @api.onchange('check_by_date')
    def _onchange_check_by_date(self):
        if self.check_by_date is False:
            self.from_date = False
            self.to_date = False

    @api.multi
    def action_search_serial(self):
        self.service_card_ids.unlink()
        self.coupon_ids.unlink()
        self.detail_service_card_ids.unlink()
        self.history_service_card_ids.unlink()

        code_customer = self.serial.strip().upper()
        serial = code_customer[0].lower() + code_customer[1:]
        # có những thẻ chữ cái đầu viết hoa.
        lot_id = self.env['stock.production.lot'].sudo().search([
            '|', '|', ('name', '=', code_customer ),
            ('name', '=', serial ),
            ('name', '=', self.serial.strip())
        ], limit=1)
        if lot_id:
            # Search Voucher
            if lot_id.product_id.x_card_type == 'voucher':
                self.check_coupon = True
                self.check_service_card = False
                # coupon info
                vals_coupon = {
                    'name': lot_id.name,
                    'stk_prdt_lot_id': lot_id.id,
                    'product_id': lot_id.product_id.id,
                    'product_release_id': lot_id.x_release_id.id,  # lần phát hành(chỉnh sửa ngày 19/02/2019)
                    'order_id': lot_id.x_order_id.id,
                    'customer_id': lot_id.x_customer_id.id,
                    'branch_id': lot_id.x_branch_id.id,
                    'life_date': lot_id.life_date,
                    'amount': lot_id.product_id.x_card_value,
                    'discount': lot_id.product_id.x_card_discount,
                    'state': lot_id.x_state,
                    'order_use_id': lot_id.x_order_use_id.id,
                    'use_customer_id': lot_id.x_use_customer_id.id,
                    'use_date': lot_id.x_order_use_id.date_order.date() if lot_id.x_order_use_id else False,
                    'search_id': self.id,
                }
                self.coupon_ids = [vals_coupon]
            # Search Service Card
            else:
                self.check_coupon = False
                self.check_service_card = True
                # card service info
                vals_card = {
                    'name': lot_id.name,
                    'stk_prdt_lot_id': lot_id.id,
                    'product_release_id': lot_id.x_release_id.id,  # lần phát hành(chỉnh sửa ngày 19/02/2019)
                    'product_id': lot_id.product_id.id,
                    'order_id': lot_id.x_order_id.id,
                    'customer_id': lot_id.x_customer_id.id,
                    'branch_id': lot_id.x_branch_id.id,
                    'life_date': lot_id.life_date,
                    'state': lot_id.x_state,
                    'total_count': lot_id.x_total_count,
                    'used_count': lot_id.x_used_count,
                    'residual_count': lot_id.x_total_count - lot_id.x_used_count,
                    'search_id': self.id,
                }
                self.service_card_ids = [vals_card]
                # card service detail info
                list_detail = []
                for line in lot_id.x_stock_production_lot_line_ids:
                    vals_card_line = {
                        'name': lot_id.name,
                        'stk_prdt_lot_id': lot_id.id,
                        'product_release_id': lot_id.x_release_id.id,
                        'product_id': lot_id.product_id.id,
                        'order_id': lot_id.x_order_id.id,
                        'customer_id': lot_id.x_customer_id.id,
                        'branch_id': lot_id.x_branch_id.id,
                        'life_date': lot_id.life_date,
                        'state': lot_id.x_state,
                        'service_id': line.product_id.id,
                        'total_count': line.total_count,
                        'used_count': line.used_count,
                        'residual_count': line.total_count - line.used_count,
                        'price_unit': line.price_unit,
                        'price_sub_total': line.price_sub_total,
                        'remain_sub_total': line.remain_sub_total,
                        'search_id': self.id,
                    }
                    list_detail.append(vals_card_line)
                self.detail_service_card_ids = list_detail
                # card service history use info
                use_line_ids = self.env['pos.use.service.line'].sudo().search([
                    ('lot_id', '=', lot_id.id)])
                list_history = []
                for use_id in use_line_ids:
                    vals_history = {
                        'using_id': use_id.use_service_id.id,
                        'date': use_id.use_service_id.date,
                        'lot_id': lot_id.id,
                        'service_id': use_id.service_id.id,
                        'qty': use_id.qty,
                        'price_unit': use_id.price_unit,
                        'amount_total': use_id.amount,
                        'employee_ids': use_id.employee_ids and [(6, 0, use_id.employee_ids.ids)] or [],
                        'order_id': use_id.use_service_id.pos_order_id.id,
                        'state': use_id.use_service_id.state,
                        'customer_sign': use_id.use_service_id.signature,
                        'note': use_id.use_service_id.note,
                        'search_id': self.id,
                        'company_id': use_id.use_service_id.company_id.id if use_id.use_service_id.company_id else False,
                    }
                    list_history.append(vals_history)
                self.history_service_card_ids = list_history
        # author: HoiHD- search customer
        if len(lot_id) == 0:
            customer_id = self.env['res.partner'].search(['|', '|', '|',
                                                          ('x_partner_code', '=', code_customer),
                                                          ('x_partner_old_code', '=', code_customer),
                                                          ('phone', '=', code_customer),
                                                          ('mobile', '=', code_customer)], limit=1)
            if len(customer_id) == 0:
                raise except_orm(WARNING, _('This code has not exist!'))

            lot_id = self.env['stock.production.lot'].sudo().search([
                ('x_customer_id', '=', customer_id.id)])
            self.check_service_card = True
            self.check_coupon = True
            self.x_name = customer_id.name
            self.x_partner_code = customer_id.x_partner_code
            self.x_partner_old_code = customer_id.x_partner_old_code
            self.x_rank_id = customer_id.x_rank_id.id
            self.x_street = customer_id.street
            self.x_vat = customer_id.vat
            self.x_phone = customer_id.phone
            self.x_email = customer_id.email
            self.x_image = customer_id.image
            self.x_company_id = customer_id.company_id.id
            for lot_customer_id in lot_id:
                if lot_customer_id.product_id.x_card_type == 'voucher':
                    voucher_values = {
                        'name': lot_customer_id.name,
                        'stk_prdt_lot_id': lot_customer_id.id,
                        'product_release_id': lot_customer_id.x_release_id.id,
                        'product_id': lot_customer_id.product_id.id,
                        'order_id': lot_customer_id.x_order_id.id,
                        'customer_id': lot_customer_id.x_customer_id.id,
                        'branch_id': lot_customer_id.x_branch_id.id,
                        'life_date': lot_customer_id.life_date,
                        'amount': lot_customer_id.product_id.x_card_value,
                        'discount': lot_customer_id.product_id.x_card_discount,
                        'state': lot_customer_id.x_state,
                        'order_use_id': lot_customer_id.x_order_use_id.id,
                        'use_customer_id': lot_customer_id.x_use_customer_id.id,
                        'use_date': lot_customer_id.x_order_use_id.date_order.date() if lot_customer_id.x_order_use_id else False,
                        'search_id': self.id,
                    }
                    self.coupon_ids = [voucher_values]
                else:
                    service_card_values = {
                        'name': lot_customer_id.name,
                        'stk_prdt_lot_id': lot_customer_id.id,
                        'product_release_id': lot_customer_id.x_release_id.id,
                        'product_id': lot_customer_id.product_id.id,
                        'order_id': lot_customer_id.x_order_id.id,
                        'branch_id': lot_customer_id.x_branch_id.id,
                        'customer_id': lot_customer_id.x_customer_id.id,
                        'life_date': lot_customer_id.life_date,
                        'state': lot_customer_id.x_state,
                        'total_count': lot_customer_id.x_total_count,
                        'used_count': lot_customer_id.x_used_count,
                        'residual_count': lot_customer_id.x_total_count - lot_customer_id.x_used_count,
                        'search_id': self.id,
                    }
                    self.service_card_ids = [service_card_values]
                    # card service detail info
                    list_detail = []
                    for line in lot_customer_id.x_stock_production_lot_line_ids:
                        values_card_line = {
                            'name': lot_customer_id.name,
                            'stk_prdt_lot_id': lot_customer_id.id,
                            'product_release_id': lot_customer_id.x_release_id.id,
                            'product_id': lot_customer_id.product_id.id,
                            'order_id': lot_customer_id.x_order_id.id,
                            'branch_id': lot_customer_id.x_branch_id.id,
                            'life_date': lot_customer_id.life_date,
                            'state': lot_customer_id.x_state,
                            'service_id': line.product_id.id,
                            'total_count': line.total_count,
                            'used_count': line.used_count,
                            'residual_count': line.total_count - line.used_count,
                            'search_id': self.id,
                            # 'company_id': lot_id.x_company_id.id,
                        }
                        list_detail.append(values_card_line)
                    self.detail_service_card_ids = list_detail
                    # card service history use info
                    use_line_ids = self.env['pos.use.service.line'].sudo().search([
                        ('lot_id', '=', lot_customer_id.id)])
                    list_history = []
                    for use_id in use_line_ids:
                        values_history = {
                            'using_id': use_id.use_service_id.id,
                            'date': use_id.use_service_id.date,
                            'lot_id': lot_customer_id.id,
                            'service_id': use_id.service_id.id,
                            'qty': use_id.qty,
                            'price_unit': use_id.price_unit,
                            'amount_total': use_id.amount,
                            'employee_ids': use_id.employee_ids and [(6, 0, use_id.employee_ids.ids)] or [],
                            'order_id': use_id.use_service_id.pos_order_id.id,
                            'state': use_id.use_service_id.state,
                            'customer_sign': use_id.use_service_id.signature,
                            'note': use_id.use_service_id.note,
                            'search_id': self.id,
                            'company_id': use_id.use_service_id.company_id.id if use_id.use_service_id.company_id else False,
                        }
                        list_history.append(values_history)
                    self.history_service_card_ids = list_history
