# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    type = fields.Selection(selection_add=[('bundle', 'Bundle')])
    x_bundle_component_ids = fields.One2many('product.bundle.component', 'product_tmpl_id', string='Bundle component')

    ''' Tạm thời không sử dụng
    @api.constrains('x_bundle_component_ids')
    def _check_bundle_component_ids(self):
        for s in self:
            if s.x_bundle_component_ids:
                total_revenue_rate = 0
                for bundle_component in s.x_bundle_component_ids:
                    if bundle_component.status == 'active':
                        total_revenue_rate += bundle_component.revenue_rate
                if total_revenue_rate != 100:
                    raise ValidationError("Phải nhập đủ tổng 100% tỷ lệ phân bổ!")'''


class ProductBundleComponent(models.Model):
    _name = 'product.bundle.component'

    name = fields.Char(string='Name')
    product_tmpl_id = fields.Many2one('product.template', ondelete='cascade', string="Bundle")
    bundle_option_ids = fields.One2many('product.bundle.option', 'bundle_component_id', string='Options')
    revenue_rate = fields.Float(string='Revenue rate (%)', help="Define when you sell a Bundle product, how many percent of the sale price is applied to this item.")
    status = fields.Selection(selection=[('active', 'Active'), ('inactive', 'Inactive')], string="Status", default='active')

class ProductBundleOption(models.Model):
    _name = 'product.bundle.option'

    bundle_component_id = fields.Many2one('product.bundle.component', string="Component", ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product')
    name = fields.Char(related='product_id.name', )
    uom_id = fields.Many2one('uom.uom', string='Unit Of Measure')
    qty = fields.Integer(string='Quantity')

    _sql_constraints = [
        ('bundle_component_id_product_id_uniq', 'unique(bundle_component_id,product_id)', 'Lựa chọn này đã tồn tại, vui lòng chọn mã sản phẩm khác !!!')
    ]

    @api.onchange('product_id')
    def on_product_changed(self):
        if self.product_id:
            if self.product_id.x_card_type in ['service_card', 'keep_card']:
                return { 'warning': {'title': 'Thông báo', 'message': 'Không chọn sản phẩm là thẻ dịch vụ và thẻ keep'}, 'value': {'product_id': False} }
            product = self.env['product.product'].sudo().browse([self.product_id.id])[0]
            self.uom_id = product.uom_id.id

    @api.constrains('qty')
    def _check_qty(self):
        for s in self:
            if s.qty <= 0:
                raise ValidationError("Số lượng phải lớn hơn 0!")