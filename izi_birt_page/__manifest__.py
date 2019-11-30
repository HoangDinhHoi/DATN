# -*- coding: utf-8 -*-
{
    'name': "Report View",

    'summary': """Base addons for report""",

    'description': """
        Nothing to description
    """,

    'author': "IZISolution",

    'category': 'Custom',
    'version': '0.1',
    'qweb': ['static/src/xml/*.xml'],
    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        'views/views.xml',
    ],
}