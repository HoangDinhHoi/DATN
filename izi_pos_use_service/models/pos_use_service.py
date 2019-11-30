# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import fields, models, api, _
from odoo.exceptions import except_orm


class PosUseService(models.Model):
    _name = 'pos.use.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    def _default_session(self):
        return self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    def _default_location(self):
        return self._default_session().config_id.material_location_id

    def _default_team(self):
        pos_session = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        return pos_session.config_id.crm_team_id.id

    def _default_branch_id(self):
        return self._default_session().branch_id

    name = fields.Char("Name", default='/')
    serial_code = fields.Char("Serial Code", track_visibility='onchange')
    date = fields.Datetime("Date", default=fields.Datetime.now, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist', "Pricelist", track_visibility='onchange', default=_default_pricelist)
    state = fields.Selection([('draft', "Draft"), ('wait_payment', "Wait Payment"), ('wait_material', "Wait Material"),
                              ('working', "Working"), ('rate', "Rate"), ('done', "Done"), ('done_refund', "Done Refund"),
                              ('cancel', "Canceled"), ('wait_confirm', "Wait Confirm"), ('approval', "Approval")], default='draft', track_visibility='onchange')
    material_request_ids = fields.One2many('pos.material.request', 'use_service_id', "Material Request")
    type = fields.Selection([('service', "Service"), ('card', "Card")], default='service', required=1)
    pos_order_id = fields.Many2one('pos.order', "Pos Order", track_visibility='onchange')
    start_date = fields.Datetime("Start Time", track_visibility='onchange')
    end_date = fields.Datetime("End Time", track_visibility='onchange')
    signature_image = fields.Binary("Signature Image", default=False, attachment=True, track_visibility='onchange')
    amount_total = fields.Float("Amount Total", compute='_compute_amount_total')
    user_id = fields.Many2one('res.users', "User", default=lambda self: self.env.uid)
    pos_session_id = fields.Many2one('pos.session', "Pos Session", default=_default_session)
    location_id = fields.Many2one('stock.location', "Location", default=_default_location)
    note = fields.Text("Note")
    use_service_ids = fields.One2many('pos.use.service.line', 'use_service_id', string="Use Service")
    payment_ids = fields.One2many(related='pos_order_id.statement_ids', string="Payment")
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id)
    crm_team_id = fields.Many2one('crm.team', "CRM Team", default=_default_team)
    keep_card = fields.Boolean("Keep card", default=False)
    pos_order_refund_id = fields.Many2one('pos.order', "Order Refund")
    branch_id = fields.Many2one('res.branch', string='Branch', default=_default_branch_id)
    x_code_search = fields.Char("Code Search")
    compare = fields.Selection(
        [('need_compare', 'Need compare'), ('compare', 'Compare'), ('valid', 'Valid'), ('invalid', 'Invalid')],
        string='Compare State', track_visibility='onchange', default='compare')
    user_compare_id = fields.Many2one('res.users', "User Compare")
    type_use = fields.Selection([('normal', "Normal"), ('product', "Product")], default='normal')

    refund_date = fields.Datetime(string='Refund Date', track_visibility='onchange')

    @api.model
    def default_get(self, fields):
        res = super(PosUseService, self).default_get(fields)
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)
        if not current_session:
            raise except_orm(("Thông báo"), ('You open session before create order.'))
        return res

    @api.onchange('location_id')
    def _onchange_location(self):
        config_id = self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1).config_id
        list = [config_id.stock_location_id.id, config_id.consign_location_id.id]
        if self.type_use == 'product':
            self.location_id = config_id.stock_location_id.id
        return {
            'domain': {'location_id': [('id', 'in', list)]}
        }

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'service':
            self.use_service_ids = False
        else:
            self.use_service_ids = False

    @api.model
    def create(self, vals):
        res = super(PosUseService, self).create(vals)
        name = 'DV' + res.company_id.partner_id.x_partner_old_code if res.company_id.partner_id.x_partner_old_code else 'DV' + res.company_id.partner_id.x_partner_code
        sequence = self.env['ir.sequence'].next_by_code('pos.use.service') or _('New')
        res.name = name + '/' + sequence[6:]
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.state not in ('draft', 'cancel'):
                raise except_orm('Thông báo!', ('Bạn không thể xóa khi khác trạng thái nháp hoặc đã hủy'))
        return super(PosUseService, self).unlink()

    @api.depends('use_service_ids.amount')
    def _compute_amount_total(self):
        for line in self:
            for tmp in line.use_service_ids:
                line.amount_total += tmp.amount

    @api.multi
    def action_search_serial(self):
        self.use_service_ids.unlink()
        serial = self.serial_code
        if serial and len(serial) > 0:
            serial = ((serial.lower().strip())[0] + (serial.strip().upper())[1:])
        else:
            raise except_orm(_('Thông báo'), _('Vui lòng nhập mã thẻ !'))
        self.x_code_search = serial
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)], limit=1)
        if lot_obj:
            if lot_obj.product_id.product_tmpl_id.x_temporary_card:
                raise except_orm('Thông báo', ('Đây là thẻ tạm không thể thu hồi được. Vui lòng tách ra thẻ khác!!!!'))
            if lot_obj.product_id.default_code == 'e_MH_SPDV' and self.type_use == 'normal':
                raise except_orm('Cảnh báo!', "Mã thẻ bạn nhập là thẻ quy đổi sản phẩm, hãy chuyển sang chức năng thu hồi thẻ sản phẩm để tiếp tục")
            if lot_obj.product_id.default_code != 'e_MH_SPDV' and self.type_use == 'product':
                raise except_orm('Cảnh báo!', "Mã thẻ bạn nhập không là thẻ quy đổi sản phẩm, hãy chuyển sang chức năng sử dụng dịch vụ để tiếp tục")
            if lot_obj.x_state != 'using':
                raise except_orm('Cảnh báo!', "Thẻ không dùng được")
            date = self.date.utcnow().date()
            if lot_obj.life_date and lot_obj.life_date + timedelta(days=1) <= date:
                raise except_orm('Thông báo!', (
                        ('Mã "%s" hết hạn vào ngày: ' + lot_obj.life_date.strftime("%d-%m-%Y")) % lot_obj.name))
            if lot_obj.x_state != 'using' and lot_obj.x_state != 'used':
                raise except_orm('Cảnh báo!', ('Thẻ không hợp lệ'))
            if lot_obj.product_id.x_card_type not in ('service_card', 'keep_card'):
                raise except_orm('Thông báo', ('Đây không phải thẻ keep, thẻ dịch vụ'))

            lines = []
            if lot_obj.product_id.product_tmpl_id.x_card_type == 'keep_card':
                self.keep_card = True
                for line in lot_obj.x_stock_production_lot_line_ids:
                    if line.total_count <= lot_obj.x_total_count:
                        price_unit = self.pricelist_id.get_product_price(line.product_id, 1,lot_obj.x_customer_id)
                        argvs = {
                            'lot_id': lot_obj.id,
                            'service_id': line.product_id.id,
                            'total_count': lot_obj.x_total_count,
                            'paid_count': line.total_count,
                            'used_count': line.used_count,
                            'qty': 1,
                            'use_service_id': self.id,
                            'lot_line_id': line.id,
                            'price_unit': price_unit
                        }
                        lines.append(argvs)
            if lot_obj.product_id.product_tmpl_id.x_card_type == 'service_card':
                for line in lot_obj.x_stock_production_lot_line_ids:
                    if line.total_count > line.used_count:
                        argvs = {
                            'lot_id': lot_obj.id,
                            'service_id': line.product_id.id,
                            'total_count': line.total_count,
                            'paid_count': line.total_count,
                            'used_count': line.used_count,
                            'qty': 1,
                            'use_service_id': self.id,
                            'lot_line_id': line.id,
                        }
                        lines.append(argvs)
            self.use_service_ids = lines
            self.partner_id = lot_obj.x_customer_id.id
        else:
            customer_obj = self.env['res.partner'].search(
                ['|', '|', '|', ('x_partner_code', '=', serial.upper().strip()), ('x_partner_old_code', '=', serial.upper().strip()),
                 ('phone', '=', serial.upper().strip()), ('mobile', '=', serial.upper().strip())])
            if customer_obj:
                lot_ids = self.env['stock.production.lot'].search([('x_customer_id', '=', customer_obj.id)])
                if not lot_ids:
                    raise except_orm("Cảnh báo",
                                     ("Không tìm thấy dịch vụ của khách hàng. VUi lòng kiểm tra lại mã khách hàng"))
                lines = []
                for line in lot_ids:
                    if line.life_date + timedelta(days=1) <= self.date.utcnow().date():
                        continue
                    if line.x_state == 'destroy':
                        continue
                    if line.product_id.product_tmpl_id.x_card_type == 'keep_card':
                        self.keep_card = True
                        for tmp in line.x_stock_production_lot_line_ids:
                            if tmp.total_count <= line.x_total_count:
                                argvs = {
                                    'lot_id': line.id,
                                    'service_id': tmp.product_id.id,
                                    'total_count': line.x_total_count,
                                    'paid_count': tmp.total_count,
                                    'used_count': tmp.used_count,
                                    'qty': 1,
                                    'use_service_id': self.id,
                                    'lot_line_id': line.id,
                                }
                                lines.append(argvs)
                    if line.product_id.product_tmpl_id.x_card_type == 'service_card':
                        for tmp in line.x_stock_production_lot_line_ids:
                            if tmp.total_count > tmp.used_count:
                                argvs = {
                                    'lot_id': line.id,
                                    'service_id': tmp.product_id.id,
                                    'total_count': tmp.total_count,
                                    'paid_count': tmp.total_count,
                                    'used_count': tmp.used_count,
                                    'qty': 1,
                                    'use_service_id': self.id,
                                    'lot_line_id': line.id,
                                }
                                lines.append(argvs)
                if len(lines) == 0:
                    raise except_orm('Cảnh báo!', ("Mã không được tìm thấy. Vui lòng kiểm tra lại"))
                self.use_service_ids = lines
                self.partner_id = customer_obj.id
            else:
                raise except_orm('Cảnh báo!', ("Mã không được tìm thấy. Vui lòng kiểm tra lại"))
        if self.type_use == 'normal':
            self.serial_code = ''
        self.partner_search_id = ''
        self._action_update_revenue_rate_use_line()

    @api.multi
    def action_confirm(self):
        if self.state != 'draft':
            return True
        if not self.partner_id:
            raise except_orm('Thông báo!', ("Thông tin khách hàng không thể bỏ trống"))
        if not self.pricelist_id:
            raise except_orm('Thông báo!', "Bạn cần điền thông tin bảng giá")
        if not self.company_id:
            raise except_orm('Thông báo!', "Bạn cần điền thông tin công ty")
        if self.type == 'card':
            return self.action_confirm_card()
        else:
            return self.action_confirm_service()

    @api.multi
    def action_confirm_card(self):
        for line in self.use_service_ids:
            if line.qty == 0:
                line.unlink()
            else:
                if self.type_use == 'normal':
                    if len(line.employee_ids) == 0:
                        raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'service_card':
                    if line.qty > (line.total_count - line.used_count):
                        raise except_orm('Cảnh báo!', ('Không thể thu hồi với số lượng dịch vụ lớn hơn số lượng khả dụng trong thẻ dịch vụ'))
        count = 0
        count_keep_card_not_paid = 0
        for line in self.use_service_ids:
            if line.qty == 0:
                continue
            if line.lot_id.x_release_id.use_type == 'fixed':
                if line.lot_id.x_customer_id.id != self.partner_id.id:
                    raise except_orm('Cảnh báo!', ("Thẻ này là đích danh không thể sử dụng cho khách hàng khác!"))
            count += 1
            if line.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                if line.paid_count < line.used_count + line.qty:
                    count_keep_card_not_paid += 1
                if line.total_count < line.used_count + line.qty:
                    raise except_orm('Thông báo!', ("Số lượng sử dụng không thể lớn hơn số lần trong thẻ"))
        if count == 0:
            raise except_orm('Cảnh báo!',
                             ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
        # Kiểm tra nêu trong danh sách có thẻ kip nào hết số lân ko
        # Nếu đã hết số lân mà vẫn dùng => tao đơn hàng bán lần đó
        if count_keep_card_not_paid > 0:
            # Tạo đơn hàng và chuyển sang trạng thái chờ thanh toán
            argvs = {
                'session_id': self.pos_session_id.id,
                'partner_id': self.partner_id.id,
                'date_order': self.date,
                'user_id': self.user_id.id,
                'x_team_id': self.crm_team_id.id,
                'pricelist_id': self.pricelist_id.id,
                'company_id': self.company_id.id,
                'x_type': 'service',
                'amount_tax': 0,
                'amount_total': self.amount_total,
                'x_rank_id': self.partner_id.x_rank_id.id,  # them rank_id added by HoiHD
                'pos_reference': self.name,  # them tham chieu vao pos_order added by HoiHD
            }
            order_id = self.env['pos.order'].create(argvs)
            self.pos_order_id = order_id.id
            for line in self.use_service_ids:
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                    if line.paid_count < line.used_count + line.qty:
                        argvss = {
                            'product_id': line.service_id.id,
                            'qty': line.used_count + line.qty - line.paid_count,
                            'price_unit': line.price_unit,
                            'discount': line.discount,
                            'order_id': order_id.id,
                            'price_subtotal': line.amount,
                            'price_subtotal_incl': line.amount,
                            'x_revenue_rate': line.revenue_rate,
                        }
                        order_line_id = self.env['pos.order.line'].create(argvss)
                        line.order_line_id = order_line_id.id
            self.state = 'wait_payment'
        # Nếu bình thường => tọa đơn xuất kho
        else:
            self.action_create_material()

    @api.multi
    def action_confirm_service(self):
        for line in self.use_service_ids:
            if line.qty == 0:
                line.unlink()
            else:
                if len(line.employee_ids) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        argvs = {
            'session_id': self.pos_session_id.id,
            'partner_id': self.partner_id.id,
            'date_order': self.date,
            'user_id': self.user_id.id,
            'x_team_id': self.crm_team_id.id,
            'pricelist_id': self.pricelist_id.id,
            'company_id': self.company_id.id,
            'x_type': 'service',
            'amount_tax': 0,
            'amount_total': self.amount_total,
            'x_rank_id': self.partner_id.x_rank_id.id,  # Added by HoiHD
            'pos_reference': self.name,  # added By HoiHD
        }
        order_id = self.env['pos.order'].create(argvs)
        for line in self.use_service_ids:
            argvss = {
                'product_id': line.service_id.id,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                'order_id': order_id.id,
                'price_subtotal': line.amount,
                'price_subtotal_incl': line.amount,
                'x_revenue_rate': line.revenue_rate,
            }
            order_line_id = self.env['pos.order.line'].create(argvss)
            line.order_line_id = order_line_id.id
        self.pos_order_id = order_id.id
        self.state = 'wait_payment'

    @api.multi
    def action_payment(self):
        ctx = self.env.context.copy()
        ctx.update({'active_id': self.pos_order_id.id})
        view = self.env.ref('izi_pos_card.pos_make_payment_coupon_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.make.payment',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_create_material(self):
        if self.state not in ('draft','wait_payment'):
            return True
        if self.amount_total > 0:
            amount = 0
            for line in self.payment_ids:
                amount += line.amount
            if amount != self.amount_total:
                raise except_orm('Thông báo!', ("Bạn cần thực hiện thanh toán hết trước khi xác nhận"))
        if not all([tmp.service_id.x_is_use_material == False for tmp in self.use_service_ids]):
            pos_material_request_obj = self.env['pos.material.request']
            employess_ids = []
            service_ids = []
            # Tạo yêu cầu nguyên vật liệu
            argvss = {
                'use_service_id': self.id,
                'date': self.date,
                'origin': self.name,
                'partner_id': self.partner_id.id,
                'picking_type_id': self.pos_session_id.config_id.picking_type_id.id,
                'company_id': self.company_id.id,
                'branch_id': self.branch_id.id,
                'location_id': self.location_id.id,
                'type_request': self.type_use,
            }
            pos_material_request_id = pos_material_request_obj.create(argvss)
            for line in self.use_service_ids:
                if line.service_id.product_tmpl_id.x_is_use_material == True:
                    for x in line.employee_ids:
                        employess_ids.append(x.id)
                    service_ids.append(line.service_id.id)
                    if not line.service_id.product_tmpl_id.x_recipe_ids:
                        raise except_orm('Cảnh báo!', "Chưa cấu hình nguyên vật liệu sử dụng cho dịch vụ %s" % line.service_id.name)
                    for tmp in line.service_id.product_tmpl_id.x_recipe_ids:
                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.uom_id.id:
                            raise except_orm("Cảnh báo!", (
                                    "Cấu hình đơn vị của nguyên vật liệu %s của dịch vụ %s khác với đơn vị tồn kho. Vui lòng kiểm tra lại" % (
                                tmp.product_id.name, line.service_id.name)))
                        argvs = {
                            'sequence': tmp.sequence,
                            'name': tmp.name,
                            'product_id': tmp.product_id.id,
                            'qty': tmp.qty * line.qty,
                            'uom_id': tmp.uom_id.id,
                            'material_request_id': pos_material_request_id.id,
                            'use': True
                        }
                        self.env['pos.material.request.line'].create(argvs)
            pos_material_request_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                            'service_ids': [(4, x) for x in service_ids], })
            # Nếu không kích hoạt xuất kho bằng tay => Tự đọng hoàn thành phiếu xuất kho luôn
            if self.pos_session_id.config_id.module_izi_pos_request_material == False and self.type == 'normal':
                pos_material_request_id.action_set_default_value()
                pos_material_request_id.action_confirm()
                pos_material_request_id.check_available()
                # Nếu đuể tồn kho thì xuất luôn
                if pos_material_request_id.check_available_field == True:
                    pos_material_request_id.action_approval()
                    pos_material_request_id.action_done()
                # Nếu thiếu tồn kho => force cho phép xuất âm
                else:
                    pos_material_request_id.force_available()
                    pos_material_request_id.action_done()
                if self.pos_session_id.config_id.module_izi_pos_customer_confirm == False:
                    return self.action_done()
                else:
                    self.state = 'working'
            else:
                self.state = 'wait_material'
        else:
            self.start_date = datetime.now()
            if self.pos_session_id.config_id.module_izi_pos_customer_confirm == False:
                return self.action_done()
            else:
                self.state = 'working'

    @api.multi
    def action_done(self):
        return self._action_done()

    @api.multi
    def _action_done(self):
        if self.branch_id.code != 'MNHN':
            self.compare = 'need_compare'
        loyal_total = 0.0
        if self.pos_order_id:
            x_journal_loyal_ids = self.pos_session_id.config_id.x_journal_loyal_ids.ids if self.pos_session_id.config_id.x_journal_loyal_ids else False
            if x_journal_loyal_ids:
                for stt in self.payment_ids:
                    if stt.journal_id.id in x_journal_loyal_ids:
                        if stt.amount > 0:
                            loyal_total += stt.amount
        if self.type == 'card':
            for line in self.use_service_ids:
                line.lot_id.x_used_count += line.qty
                service_card_detail_obj = self.env['stock.production.lot.line'].search(
                    [('stock_production_lot_id', '=', line.lot_id.id), ('product_id', '=', line.service_id.id)])
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                    if loyal_total > 0:
                        service_card_detail_obj.used_count += line.qty
                        service_card_detail_obj.total_count += (line.used_count + line.qty - line.paid_count)
                        service_card_detail_obj.price_sub_total += line.revenue_rate * loyal_total
                        service_card_detail_obj.remain_sub_total = 0
                    else:
                        service_card_detail_obj.used_count += line.qty
                        if service_card_detail_obj.remain_sub_total > line.qty * service_card_detail_obj.price_unit:
                            service_card_detail_obj.remain_sub_total -= line.qty * service_card_detail_obj.price_unit
                        else:
                            service_card_detail_obj.remain_sub_total = 0
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'service_card':
                    service_card_detail_obj.used_count += line.qty
                    if service_card_detail_obj.remain_sub_total > line.qty * service_card_detail_obj.price_unit:
                        service_card_detail_obj.remain_sub_total -= line.qty * service_card_detail_obj.price_unit
                    else:
                        service_card_detail_obj.remain_sub_total = 0
                if line.lot_id.x_total_count == line.lot_id.x_used_count:
                    line.lot_id.x_state = 'used'
        self.state = 'done'
        self.end_date = datetime.now()
        if self.pos_order_id:
            if self.pos_order_id.state not in ('done', 'paid', 'invoiced'):
                self.pos_order_id.state = 'invoiced'
                return self.pos_order_id.action_confirm_order()

        # #thêm lịch sử tồn thẻ
        # product_lot_inventory_history_obj = self.env['product.lot.inventory.history']
        # if self.type == 'card':
        #     for line in self.use_service_ids:
        #         stk_prdt_lot_line_id = self.env['stock.production.lot.line'].search(
        #             [('product_id', '=', line.service_id.id), ('stock_production_lot_id', '=', line.lot_id.id)])
        #         product_lot_inventory_history_obj.create(dict(
        #             lot_id=line.lot_id.id,
        #             customer_id=self.partner_id.id,
        #             card_code=line.lot_id.name,
        #             card_total_count=line.lot_id.x_total_count,
        #             card_used_count=line.lot_id.x_used_count,
        #             product_id=line.service_id.id,
        #             detail_id=stk_prdt_lot_line_id.id if stk_prdt_lot_line_id else False,
        #             product_total_count=stk_prdt_lot_line_id.total_count,
        #             product_used_count=stk_prdt_lot_line_id.used_count,
        #             date=self.date.date(),
        #             date_time=self.date,
        #             origin=self.name,
        #             qty_exchange=line.qty * -1
        #         ))

    @api.multi
    def action_back(self):
        for line in self.pos_order_id.statement_ids:
            line.unlink()
        for line in self.pos_order_id.lines:
            line.unlink()
        self.pos_order_id.unlink()
        self.state = 'draft'

    @api.multi
    def refund(self):
        if self.state != 'done':
            return
        if self.type == 'card':
            for line in self.use_service_ids:
                if not line.lot_id:
                    raise except_orm('Cảnh báo!', "Thẻ này đã được refund ở đơn bán ra. Bạn không thể thao tác tiếp trên đơn này!")
        self.name = 'RF_' + self.name
        self.refund_date = datetime.now()
        self.state = 'wait_confirm'

    @api.multi
    def action_confirm_refund(self):
        if self.state != 'wait_confirm':
            return
        self.state = 'approval'

    @api.multi
    def action_not_confirm_refund(self):
        if self.state != 'wait_confirm':
            return
        self.name = self.name[3:]
        self.refund_date = False
        self.state = 'done'

    @api.multi
    def action_done_refund(self):
        if self.state != 'approval':
            return
        if self.pos_order_id:
            self.pos_order_id.refund()
            pos_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
            self.pos_order_refund_id = pos_refund.id
        loyal_total = 0.0
        if self.pos_order_refund_id:
            x_journal_loyal_ids = self.pos_session_id.config_id.x_journal_loyal_ids.ids if self.pos_session_id.config_id.x_journal_loyal_ids else False
            if x_journal_loyal_ids:
                for stt in self.payment_ids:
                    if stt.journal_id.id in x_journal_loyal_ids:
                        if stt.amount != 0:
                            loyal_total += stt.amount
        if self.type == 'card':
            for line in self.use_service_ids:
                line.lot_id.x_used_count -= line.qty
                service_card_detail_obj = self.env['stock.production.lot.line'].search(
                    [('stock_production_lot_id', '=', line.lot_id.id), ('product_id', '=', line.service_id.id)])
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'keep_card':
                    if loyal_total < 0:
                        service_card_detail_obj.used_count -= line.qty
                        service_card_detail_obj.total_count -= (line.used_count + line.qty - line.paid_count)
                        service_card_detail_obj.price_sub_total += line.revenue_rate * loyal_total
                        service_card_detail_obj.remain_sub_total = 0
                    else:
                        service_card_detail_obj.used_count -= line.qty
                        service_card_detail_obj.remain_sub_total += line.qty * service_card_detail_obj.price_unit
                if line.lot_id.product_id.product_tmpl_id.x_card_type == 'service_card':
                    service_card_detail_obj.used_count -= line.qty
                    service_card_detail_obj.remain_sub_total += line.qty * service_card_detail_obj.price_unit
                line.lot_id.x_state = 'using'
        for line in self.material_request_ids:
            line.action_refund()
        self.state = 'done_refund'
        if self.pos_order_refund_id:
            self.pos_order_refund_id.send_refund()
            self.pos_order_refund_id.confirm_refund()
            return self.pos_order_refund_id.done_refund()

        if self.origin:
            service_booking = self.env['service.booking'].search([('name', '=', self.origin)])
            if len(service_booking) == 1:
                #Hủy Booking
                service_booking.state = 'cancel'

        #thêm lịch sử tồn thẻ
        # product_lot_inventory_history_obj = self.env['product.lot.inventory.history']
        # if self.type == 'card':
        #     for line in self.use_service_ids:
        #         stk_prdt_lot_line_id = self.env['stock.production.lot.line'].search(
        #             [('product_id', '=', line.service_id.id), ('stock_production_lot_id', '=', line.lot_id.id)])
        #         product_lot_inventory_history_obj.create(dict(
        #             lot_id=line.lot_id.id,
        #             customer_id=self.partner_id.id,
        #             card_code=line.lot_id.name,
        #             card_total_count=line.lot_id.x_total_count,
        #             card_used_count=line.lot_id.x_used_count,
        #             product_id=line.service_id.id,
        #             detail_id=stk_prdt_lot_line_id.id if stk_prdt_lot_line_id else False,
        #             product_total_count=stk_prdt_lot_line_id.total_count,
        #             product_used_count=stk_prdt_lot_line_id.used_count,
        #             date=self.date.date(),
        #             date_time=self.date,
        #             origin=self.name,
        #             qty_exchange=line.qty
        #         ))

    @api.multi
    def action_cancel(self):
        if self.state != 'wait_material':
            return
        self.action_back()
        for line in self.material_request_ids:
            line.action_cancel()
        self.state = 'cancel'

    @api.onchange('use_service_ids')
    # Tính revenue_rate của sản phẩm dịch vụ vào trong use_service_line
    # Cập nhật lại trường revenue_rate trên từng order_line
    def _action_update_revenue_rate_use_line(self):
        total_revenue = 0
        total = 0
        count = len(self.use_service_ids)
        print(count)
        for line in self.use_service_ids:
            total += line.amount
        for line in self.use_service_ids:
            count -= 1
            if count != 0:
                if total == 0:
                    line.revenue_rate = 0
                    total_revenue += 0
                else:
                    line.revenue_rate = line.amount / total
                    total_revenue += line.amount / total
            else:
                if total == 0:
                    line.revenue_rate = 0
                else:
                    line.revenue_rate = 1 - total_revenue

    @api.multi
    def action_compare(self):
        if self.env.user.branch_id.code != 'MNHN':
            raise except_orm('Thông báo', 'Bạn không có quyền thực hiện hành động này!')
        ctx = self.env.context.copy()
        ctx.update({'default_use_service_id': self.id})
        view = self.env.ref('izi_pos_use_service.pos_use_service_inherit_compare_transient_form_view')
        return {
            'name': 'Order',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.use.service.compare.transient',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
