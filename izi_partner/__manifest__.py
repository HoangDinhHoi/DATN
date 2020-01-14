# -*- coding: utf-8 -*-
{
    'name': "izi_partner",

    'summary': """
        - Thêm các trường liên quan và được dùng chung của res_partner
         """,

    'description': """
        - Thêm các trường liên quan và được dùng chung của res_partner
    """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customer Relationship Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm'],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'data/sequence.xml',
        # 'security/partner_security.xml',#tạm thời tắt đi
    ],
}
