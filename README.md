# Waterbug

Waterbug is a command-line tool for accessing water-usage data from the [San Francisco Public Utilities Commission](http://www.sfwater.org/).  You'll need an [existing account](https://myaccount.sfwater.org/). This works for me, but I haven't tried it with other accounts, other operating systems, etc.  Your mileage may vary, caveat emptor.  Pull requests welcome.

## Overview

By default, Waterbug returns the most recent ten days of usage.  So `python waterbug.py` results in:

    Water Use in Gallons, 1/20/2016 through 1/29/2016:
    ======================================================
    1/20    127
    1/21    134
    1/22    149
    1/23    123
    1/24    157
    1/25    188
    1/26    134
    1/27    142
    1/28    104
    1/29    164

To see the most recent 30 days of water usage, use `python waterbug.py recent 30`.

To see usage between particular dates, use (for example) `python waterbug.py range 2016-01-01 2016-01-30`. Formatting for `start_date` and `end_date` is flexible, but YYYY-MM-DD is sure to work.

Use `-g` option to output a [termgraph](https://github.com/mkaz/termgraph) like the following:

    1/26: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 134.00
    1/27: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 142.00
    1/28: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 104.00

Use `-x` to save the results to `water_usage.xls` in the same directory as Waterbug.

## Usage

    Usage:
        waterbug [options]
        waterbug [options] recent <days>
        waterbug [options] range <start_date> <end_date>
    Options:
        -h --help         Show this information.
        --version         Show version.
        -x, --xls         Output xls file
        -g, --graph       Output termgraph

