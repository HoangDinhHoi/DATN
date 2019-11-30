# -*- coding: utf-8 -*-
{
    'name': "Bundle Management",

    'summary': """
        - Bundle Management
        """,

    'description': """
        - Bundle Management
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','product', 'izi_pos'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_bundle_view.xml',
        'views/pos_product_bundle_view.xml',
    ],
}