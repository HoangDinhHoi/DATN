# -*- coding: utf-8 -*-
{
    'name': "izi_pos",

    'summary': """
        - Thêm các trường liên quan và dùng chung của Point of Sale
        """,

    'description': """
        - Thêm các trường liên quan và dùng chung của Point of Sale
    """,

    'author': "IZISoluiton",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_branch'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/custom_pos_session_view.xml',
        'views/inherit_pos_config.xml',
        'views/pos_order_view.xml',
        'security/pos_security.xml',
        'views/inherit_utm_and_jouranl_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}