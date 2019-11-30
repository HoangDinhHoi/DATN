# -*- coding: utf-8 -*-
{
    'name': "POS Customer Confirm",

    'summary': """
        - POS Customer Confirm
        """,

    'description': """
        - POS Customer Confirm
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_use_service', 'izi_pos_card', 'web_digital_sign', 'izi_new_widget'],

    # always loaded
    'data': [
        # 'views/signature_view.xml',
        'views/pos_order_view.xml',
        'views/pos_config_view.xml',
        'views/pos_use_service_view.xml',
        'views/pop_up_orrder_signature_view.xml',
        'views/pop_up_use_service_signature_view.xml',
        'security/ir.model.access.csv',
    ],
}