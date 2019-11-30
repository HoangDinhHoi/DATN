# -*- coding: utf-8 -*-
{
    'name': "Pos payment by bank",

    'summary': """
        - Config journal bank \n
        - Payment by bank
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
    'depends': ['base','izi_pos'],

    # always loaded
    'data': [
        'views/pos_bank_card.xml',
        'wizard/pos_payment.xml',
        'views/pos_order_view.xml',
        'security/ir.model.access.csv',
        'security/payment_bank.xml',
    ],
}
