#!/usr/bin/env python3

'''
Get available ips of hosts blocked by GFW from
https://github.com/racaljk/hosts
'''

import logging
import os
import re
import requests
import sys

r_ = requests.get('https://raw.githubusercontent.com/racaljk/hosts/master/hosts')
re_ = re.compile(r'((\d{1,3}\.){3}\d{1,3})\s+([^#\s]+)\s*(#.*)?')
lines_ = r_.text.split(u'\n')
hosts_list = { m_.group(3).lower(): m_.group(1) \
        for m_ in \
            [msv_ for msv_ in \
                [re_.match(ms_) for ms_ in lines_] \
        if msv_ != None] }
