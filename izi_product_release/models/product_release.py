# -*- coding: utf-8 -*-

# author: HoiHD
from odoo import fields, models, api, _
from odoo.exceptions import except_orm, ValidationError, AccessDenied


class ProductRelease(models.Model):
    _name = 'product.release'
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    branch_id = fields.Many2one('res.branch', string=_('Receive Unit'), track_visibility='onchange',
                                default=lambda self: self.env.user.branch_id.id)
    card_id = fields.Many2one('product.product', string=_('Card Type'), track_visibility='onchange')
    product_type = fields.Char(string=_('Product Type'), track_visibility='onchange')
    release_reason_id = fields.Many2one('product.release.reason', string="Product Release Reason", track_visibility='onchange')
    card_type = fields.Char(string='Card Type', track_visibility='onchange')
    preview_prefix_code = fields.Char(string=_('Preview prefix of Code'), compute='_preview_prefix_code')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id, track_visibility='onchange')
    name = fields.Char(default='NEW', readonly=True, copy=False, track_visibility='onchange')
    campaign_id = fields.Many2one('utm.campaign', string=_('Campaign'), track_visibility='onchange')
    blank_card_id = fields.Many2one('product.product', string=_('Blank Card'))
    quantity = fields.Integer(string=_('Quantity'), default=1, track_visibility='onchange')
    release_location_id = fields.Many2one('stock.location', string='Release Location')
    location_id = fields.Many2one('stock.location', string='Location')
    date = fields.Date(string=_('Date'), default=fields.Date.today(), track_visibility='onchange')
    expired_type = fields.Selection([
        ('fixed', _('Fixed')),
        ('flexible', _('Flexible'))
    ], string=_('Expired Type'), default='flexible', track_visibility='onchange')
    expired_date = fields.Date(string=_('Expired Date'), track_visibility='onchange')
    validity = fields.Integer(string=_('Number of active days(month)'), default=0, track_visibility='onchange')
    use_type = fields.Selection([
        ('fixed', _('Fixed Name')),
        ('flexible', _('Flexible'))
    ], string=_('Use Type'), default='fixed', track_visibility='onchange')

    state = fields.Selection(selection=(('draft', 'Draft'),
                                        ('created', 'Created'),
                                        ('activated', "Activated"),
                                        ('transferring', 'Transferring'),
                                        ('done', 'Done'),
                                        ('cancel', "Cancel"),), default='draft', string=_('Status'), track_visibility='onchange')
    stock_production_lot_ids = fields.One2many('stock.production.lot', 'x_release_id', string=_('Stock Production Lot'))
    preview_code = fields.Char(string=_('Preview Code'), compute='_preview_code')
    picking_ids = fields.One2many('stock.picking', 'x_product_release_id', string='Stock Picking')
    count_picking = fields.Integer(string=_('Transfers'), readonly=True,
                                   store=True, compute='_compute_count_picking', default=0)
    reference = fields.Char(string=_('Reference'))

    @api.onchange('release_location_id')
    def _onchange_release_location(self):
        """
        :return: mặc định kho phát hành là kho nhận
        """
        if self.release_location_id:
            self.location_id = self.release_location_id

    # Tính toán số dịch chuyển từ stock.picking
    @api.multi
    @api.depends('picking_ids')
    def _compute_count_picking(self):
        for item in self:
            item.count_picking = len(item.picking_ids)

    # Tạo mã cho đợt phát hành
    @api.model
    def create(self, vals):
        # Chỉ có quản trị viên mới được phát hành thẻ
        is_superuser = self.env.user.has_group('base.group_system')
        if not is_superuser:
            raise AccessDenied("Bạn không có quyền tạo đợt phát hành thẻ dịch vụ!")
        if vals.get('name', 'NEW') == 'NEW':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.release') or 'NEW'
        return super(ProductRelease, self).create(vals)

    # Không cho xóa bản ghi ở trạng thái khác nháp
    @api.multi
    def unlink(self):
        for line in self:
            if line.state not in ('draft', 'created'):
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(ProductRelease, self).unlink()

    # nếu nhân bản thì mã tự sinh sẽ tăng
    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('product.release') or 'NEW'
        return super(ProductRelease, self).copy(default)

    # nếu phương thức hết hạn là linh hoạt thì ẩn ngày hết hạn, nếu ngược lại thì ẩn số tháng hiệu lực
    @api.onchange('expired_type', 'expired_date', 'validity')
    def _onchange_check(self):
        if self.expired_type == 'flexible':
            self.expired_date = False
        else:
            self.validity = 0

    # Kiểm tra số tháng hiệu lực của thẻ, phải lớn hơn 0
    @api.constrains('card_id', 'expired_type', 'validity')
    def _check_validity(self):
        if self.card_id.x_card_type == 'voucher':  # added By HoiHD: Chỉ bắt > 0 khi thẻ là coupon và voucher
            if self.expired_type == 'flexible' and (self.validity <= 0 or self.validity is False):
                raise ValidationError(_(u"Số tháng hết hạn phải lớn hơn 0 !!!"))
        else:
            if self.expired_type is False:
                raise ValidationError('Vui lòng chọn phương thức hết hạn!')
            if self.expired_type == 'flexible' and (self.validity < 0 or self.validity is False):
                raise ValidationError('Số tháng hết hạn không được âm hoặc bỏ trống!')

    # Kiểm tra ngày nhập vào, nếu ngày hiện tại lớn hơn ngày hết hạn thì báo lỗi
    @api.constrains('expired_type', 'expired_date', 'date')
    def _check_expired_date(self):
        if self.expired_type == 'fixed' and self.date > self.expired_date:
            raise ValidationError(_(u"Ngày hết hạn phải lớn hơn ngày phát hành !!!"))

    # Trả về 2 field lấy theo loại thẻ, nếu loại thẻ là dịch vụ thì trường phôi bị ẩn đi
    @api.onchange('card_id')
    def _onchange_product_type(self):
        if self.card_id:
            self.product_type = self.card_id.type
            self.card_type = self.card_id.x_card_type
            if self.card_id.type == 'consu':
                self.blank_card_id = False

    # Hiển thị tiền tố của mã.
    @api.depends('release_reason_id', 'branch_id', 'blank_card_id', 'date', 'card_id')
    def _preview_prefix_code(self):
        for line in self:
            if all([line.card_id, line.release_reason_id, line.branch_id, line.date]):
                prefix = ""
                month = line.date.month
                release_reason_code = str(line.release_reason_id.code)
                receive_unit_code = str(line.branch_id.code)
                if line.card_id.product_tmpl_id.type == 'product':
                    prefix = 'p'
                elif line.card_id.product_tmpl_id.type == "consu":
                    prefix = 'e'
                if line.branch_id.code:
                    line.preview_prefix_code = prefix + release_reason_code + receive_unit_code + str(line.date.year)[2:] + (str(month) if month > 10 else '0' + str(month)) + 'x x x x x x'
                else:
                    raise except_orm(_('Thông báo'), _("Đơn vị nhận không có mã."))

    # Hiển thị tiền tố của mã
    @api.onchange('release_reason_id', 'branch_id', 'blank_card_id', 'date', 'card_id')
    def _onchange_preview_prefix_code(self):
        for line in self:
            if all([line.card_id, line.release_reason_id, line.branch_id, line.date]):
                prefix = ""
                month = line.date.month
                release_reason_code = str(line.release_reason_id.code)
                receive_unit_code = str(line.branch_id.code)
                if line.card_id.product_tmpl_id.type == 'product':
                    prefix = 'p'
                if line.card_id.product_tmpl_id.type == 'consu':
                    prefix = 'e'

                if line.branch_id.code:
                    line.preview_prefix_code = prefix + release_reason_code + receive_unit_code + str(line.date.year)[2:] + (str(month) if month > 10 else '0' + str(month)) + 'x x x x x x'
                else:
                    raise except_orm(_('Thông báo'), _("Receive Unit don't have code."))

    # Kiểm tra số lượng phôi nhập vào
    @api.onchange('quantity')
    def _constraint_quantity_blank_card(self):
        if self.blank_card_id:
            total_availability = self.env['stock.quant']._get_available_quantity(self.blank_card_id, self.release_location_id)
            if self.quantity and (self.quantity > total_availability):
                raise except_orm(_('ATTENTION!!!'), _('The number of blank card in the current stock is ')+str(int(total_availability))+_('. Please re-enter the quantity or re-update quantity of blank card in stock.'))

    # Kiểm tra số lượng phôi nhập vào, khi ấn vào các action create, write, unlink
    @api.constrains('quantity')
    def _constraint_quantity_blank_card(self):
        if self.blank_card_id:
            total_availability = self.env['stock.quant']._get_available_quantity(self.blank_card_id, self.release_location_id)
            if self.quantity and (self.quantity > total_availability):
                raise except_orm('ATTENTION!!!', 'The number of blank card in the current stock is ' + str(int(total_availability)) + '. Please re-enter the quantity.')
