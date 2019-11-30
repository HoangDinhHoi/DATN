# -*- coding: utf-8 -*-
# author: HoiHD
from odoo import fields, models, api, _
from odoo.exceptions import except_orm


class InheritProduct(models.Model):
    _inherit = 'product.template'

    x_is_blank_card = fields.Boolean(_('Is Blank Card'), default=False)
    x_duration = fields.Float(string='Duration', default=0)

    x_card_type = fields.Selection([
        ('none', 'None'),
        ('keep_card', _('Keep Card')),
        ('service_card', _('Service Card')),
        ('voucher', _('Voucher'))
    ], string=_('Card Type'), default='none')
    x_card_value = fields.Float(string=_('Value'))
    x_card_discount = fields.Float(string=_('Discount(%)'))
    x_card_count = fields.Integer(string=_('Use Times'))
    x_use_policy = fields.Text(string=_('Use Policy'))
    x_show_in_app = fields.Boolean(string=_('Show in app'), default=False)
    x_product_card_ids = fields.One2many('product.card.allow', 'product_id', string=_('Product & Service'))
    x_product_category_card_ids = fields.One2many('product.category.card.allow', 'product_id', string=_('Product & Service Group'))
    x_feature_product = fields.Many2one('product.features',string=_('Feature Product'))
    x_temporary_card = fields.Boolean(string='Temporary card')


    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', _('The code must be unique!'))]

    @api.constrains('x_card_type','x_card_count')
    def _constrains_card_count_keep(self):
        for item in self:
            if item.x_card_type == 'keep_card' and self.x_card_count <= 0:
                raise except_orm('Thông báo', 'Vui lòng cấu hình số lượng áp dụng cho thẻ keep bạn vừa tạo.')

    # # check default_code must be unique or not, and dont allow any space in it!
    # @api.model
    # def create(self, vals):
    #     if ' ' in str(vals.get('default_code')):
    #         raise except_orm('Warning!', _('The code do not allow any space!'))
    #     vals['default_code'] = str(vals.get('default_code')).upper().strip()
    #     return super(InheritProduct, self).create(vals)
    #
    #
    # @api.multi
    # def write(self, vals):
    #     if vals.get('default_code'):
    #         if ' ' in str(vals.get('default_code')):
    #             raise except_orm('Warning!', _('The code do not allow any space!'))
    #         vals['default_code'] = str(vals.get('default_code')).upper().strip()
    #     return super(InheritProduct, self).write(vals)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    _sql_constraints = [('default_code_uniq', 'unique(default_code)', _('The code must be unique!'))]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        BundleComponentObj = self.env['product.bundle.component']
        domain = args + ['|', ('name', 'ilike', name), ('default_code', 'ilike', name.upper())]
        context = self._context
        if 'x_type_product' in context:
            if context['x_type_product'] == 'bundle':
                domain += [('type', '=', 'bundle')]
            if context['x_type_product'] == 'not_bundle':
                domain += [('type', '!=', 'bundle')]
        if 'tracking' in context:
            if context['tracking'] == 'none':
                domain += [('tracking', '=', 'none')]

        products = self.sudo().search_read(domain, fields=['id', 'default_code', 'name'], limit=limit)
        if 'bundle_component_id' in context:
            bundle_component_id = context['bundle_component_id']
            bundle_component = BundleComponentObj.search([('id', '=', bundle_component_id)], limit=1)
            bundle_option_ids = []
            for bundle_option in bundle_component.bundle_option_ids:
                bundle_option_ids.append(bundle_option.product_id.id)
            products = self.sudo().search_read(domain + [('id', 'in', bundle_option_ids)], fields=['id', 'default_code', 'name'], limit=limit)

        result = []
        for product in products:
            result.append([product['id'], '[' + str(product['default_code']) + '] ' + str(product['name'])])
        res = result
        return res

    # # Check default_code: do not allow any space in code and the code must be unique!
    # @api.model
    # def create(self, vals):
    #     if ' ' in str(vals.get('default_code')):
    #         raise except_orm('Warning!', _('The code do not allow any space!'))
    #     vals['default_code'] = str(vals.get('default_code')).upper().strip()
    #     return super(ProductProduct, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     if vals.get('default_code'):
    #         if ' ' in str(vals.get('default_code')):
    #             raise except_orm('Warning!', _('The code do not allow any space!'))
    #         vals['default_code'] = str(vals.get('default_code')).upper().strip()
    #     return super(ProductProduct, self).write(vals)
    #
