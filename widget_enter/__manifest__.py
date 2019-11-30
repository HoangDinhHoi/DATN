{
    'name': 'Enter widget',
    'description': 'Enter to submit widget',
    'version':'1.0',
    'author':'IZISolution',

    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
    ],
    'website': '',
    'depends': ['web'],
    "qweb": [
        'static/src/xml/templates.xml',
    ],
    'application': False,
}
