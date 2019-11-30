# -*- coding: utf-8 -*-
# Created by Hoanglv on 8/18/2019

import re


class Email(object):

    @staticmethod
    def validate_email(email, error_message=''):
        pattern = r'[\w\.]+@[\w]{2,6}.([a-z]{2,6}){1,3}'
        if not re.search(pattern, email):
            raise Exception(error_message or 'Email format is incorrect')
        return True
