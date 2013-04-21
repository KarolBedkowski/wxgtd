# -*- coding: utf-8 -*-
""" Validators for wx widgets.

Copyright (c) Karol Będkowski, 2006-2013

This file is part of wxGTD

This is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, version 2.
"""
__author__ = "Karol Będkowski"
__copyright__ = "Copyright (c) Karol Będkowski, 2006-2013"
__version__ = '2013-04-21'
__all__ = ['ValidatorDv', 'Validator', 'ValidatorDate', 'ValidatorTime',
		'ValidatorColorStr']


from .validator import Validator, ValidatorDv, ValidatorDate, ValidatorTime, \
		ValidatorColorStr
