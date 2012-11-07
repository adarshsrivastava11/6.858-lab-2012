#!/usr/bin/env python

import sys
import htmlfilter

print htmlfilter.filter_html(sys.stdin.read())

