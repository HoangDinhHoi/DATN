# -*- coding: utf-8 -*-
{
    'name': "Pos card and coupon",

    'summary': """
        + Sell card and coupon \n
        + Edit journal payment by coupon \n
        + Payment by coupon
        """,

    'description': """
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_product_release','izi_pos'],

    # always loaded
    'data': [
        'views/account_journal_view.xml',
        'views/pos_order_view.xml',
        'wizard/pos_payment.xml',
        'views/pos_rule_card_expirate.xml',
        'security/ir.model.access.csv',
    ],
}