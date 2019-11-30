# -*- coding: utf-8 -*-
{
    'name': "Product Custom",

    'summary': """
        - Inherit Product \n
        - Add any fields into Product \n
        - Config card and coupon 
        """,

    'description': """
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product', 'stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_card_allow.xml',
        'views/product_category_card_allow.xml',
        'views/product.xml',
        'views/product_menu_customize.xml',
        'views/product_template.xml',
        'views/product_category_view.xml',
        'views/product_features_view.xml',
        'views/production_lot_view.xml',
        ],
}