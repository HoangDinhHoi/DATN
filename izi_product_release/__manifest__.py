# -*- coding: utf-8 -*-
{
    'name': "Release card and coupon,voucher",

    'summary': """
        - Release card and coupon,voucher \n
        - Reason release \n
        - Edit table lot
        """,
    'description': """
    """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_partner','izi_pos','izi_product','stock', 'izi_stock_transfer', 'izi_branch'],

    # always loaded
    'data': [
        'data/ir_sequence_data.xml',
        'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/stock_production_lot.xml',
        'views/product_release_reason.xml',
        'views/product_release.xml',
    ],
}
