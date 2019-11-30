# -*- coding: utf-8 -*-
{
    'name': "Search service card, coupon or customer",

    'summary': """
        Search service card, coupon or customer
        """,

    'description': """
        - Tìm kiếm các thông tin có liên quan đến thẻ.
        - Lịch sử tồn thẻ
        - Lịch sử tách, đổi thẻ
        - Lịch sử đổi, sử dụng dịch vụ
        - Tìm kiếm các thẻ và các chức năng trên có liên quan đến khách hàng.
    """,

    'author': "HoiHD",
    'website': "http://www.fb.com/hoihandsome",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'search',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_customer_confirm', 'web_digital_sign', 'izi_new_widget'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pos_search.xml',
    ],
}
