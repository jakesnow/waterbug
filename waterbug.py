#!/usr/bin/env python
# coding=utf-8
'''
Waterbug

Waterbug is a command-line tool for accessing water-usage data from 
San Francisco Public Utilities Commission.  By default, the script returns
the most recent ten days of usage.  Default output is text to the terminal.

Use the '-g' flag to output a termgraph like the following:

1/26: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 134.00
1/27: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 142.00
1/28: ▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇▇ 104.00

Formatting for start_date and end_date is flexible, but YYYY-MM-DD is sure to work.

Usage:
    waterbug [options]
    waterbug [options] recent <days>
    waterbug [options] range <start_date> <end_date>

Options:
    -h --help         Show this information.
    --version         Show version.
    -x, --xls         Output xls file
    -g, --graph       Output termgraph
'''

__title__ = 'waterbug'
__version__ = '0.1'
__author__ = 'Jake Snow'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Jacob A. Snow'

import sys
import getpass

import requests
from bs4 import BeautifulSoup

from datetime import datetime, timedelta
from dateutil.parser import *
from dateutil.relativedelta import relativedelta

from docopt import docopt

from termgraph import main as graph

# USERID = "[SF WATER USERNAME]"
# PASSWORD = "[SF WATER PASSWORD]"

def get_credentials():
    '''
    If credentials are hard-coded constants, return them.  Otherwise 
    prompt the user.
    '''
    try:
        userid = USERID
    except (NameError):
        userid = raw_input("Please enter your SF Water login: ")
    try:
        password = PASSWORD
    except (NameError):
        password = getpass.getpass("Please enter your SF Water password: ")
    return (userid, password)

def loginerror():
    print "\n====================================="
    print "Your login or password was incorrect."
    print "====================================="

def datetime_to_day(date_time):
    '''convert datetime object to string of the form "MM/DD/YYYY'''
    day = "%s/%s/%s" % (date_time.month, date_time.day, date_time.year)
    return day

def fix_future_date(datetime):
    '''If start date or end date is in the future, put them in last year.'''
    if datetime > datetime.today():
        previous_year = datetime - relativedelta(years=1)
        return previous_year
    else:
        return datetime

def output_mode(arguments):
    if arguments['--graph']:
        return "graph"
    elif arguments['--xls']:
        return "xls"
    else:
        return "text"

def terminal_output_header(start, end):
    print "\nWater Use in Gallons, %s through %s:" % (start, end)
    print "======================================================"

def output(water, mode, start_datetime, end_datetime):
    start = datetime_to_day(start_datetime)
    end = datetime_to_day(end_datetime)
    if mode == "text":
        terminal_output_header(start, end)
        for day_use_pair in water:
            print day_use_pair
    elif mode == "graph":
        terminal_output_header(start, end)
        graph(water)
        # print water
    elif mode == "xls":
        xls_file = "Date\tConsumption in GALLONS\n"
        for day_use_pair in water:
            xls_file += day_use_pair + "\n"
        write_xls = open("water_usage.xls", 'wb')
        write_xls.write(xls_file.encode("utf-8"))
        write_xls.close()

def init(arguments):
    '''
    Pull start and end date in from command line arguments, depending on 
    whether range or recent is specified in arguments.  Default is to show the 
    last ten days of usage.
    '''
    if arguments['range']:
        start_datetime = parse(arguments['<start_date>'])
        end_datetime = parse(arguments['<end_date>'])

        start_datetime = fix_future_date(start_datetime)
        end_datetime = fix_future_date(end_datetime)

        # If start date is later than end date, switch them.
        if start_datetime > end_datetime:
            start_datetime, end_datetime = end_datetime, start_datetime

    else:
        if arguments['<days>']:
            days = arguments['<days>']
        else:
            days = 10

        start_datetime = datetime.today() - timedelta(days=int(days))
        end_datetime = datetime.today() - timedelta(days=1)

    return (start_datetime, end_datetime)

def water_usage(userid, password, start_datetime, end_datetime):
    '''
    Pull water usage from sfwater.org and return list of tab-separated values.
    '''

    start_day = datetime_to_day(start_datetime)
    end_day = datetime_to_day(end_datetime)

    with requests.Session() as c:

        waterbill_url = "https://myaccount.sfwater.org/~~~\
            QUFBQUFBV1ZFb1Evbm1zMEpWSzRCMmYrcEZtT05zMkpJMHdEM2VqQnNPTlpEUjFlR2c9PQ==ZZZ"
        r = c.get("https://myaccount.sfwater.org")

        soup=BeautifulSoup(r.content, "html.parser")

        # Extract values from page that must be in the login POST
        VIEWSTATE=soup.find(id="__VIEWSTATE")['value']
        VIEWSTATEGENERATOR=soup.find(id="__VIEWSTATEGENERATOR")['value']
        EVENTVALIDATION=soup.find(id="__EVENTVALIDATION")['value']

        # Populate login POST
        login_data = {"__VIEWSTATE":VIEWSTATE,
            "__VIEWSTATEGENERATOR":VIEWSTATEGENERATOR,
            "__EVENTVALIDATION":EVENTVALIDATION,
            "tb_USER_ID":userid,
            "tb_USER_PSWD":password,
             "btn_SIGN_IN_BUTTON":"Sign in"}
        
        # Submit login
        login = c.post(waterbill_url, data = login_data)
        
        # Raise exception if login credentals fail
        if "<h2>Sign In Failure</h2>" in login.content:
            raise ValueError('Sign in failure')

        my_account = c.get("https://myaccount.sfwater.org/~~~QUFBQUFBV3RCUW5sMFltOXVXNGtBUVBKVVhRQkRxVGFmU2JRVGVBbGJ0Z2tWWkNRRFE9PQ==ZZZ")   
        newsoup = BeautifulSoup(my_account.content, "html.parser")
        
        # Extract values from page that must be in the data-request POST
        VIEWSTATE = newsoup.find(id="__VIEWSTATE")['value']
        VIEWSTATEGENERATOR = newsoup.find(id="__VIEWSTATEGENERATOR")['value']
        EVENTVALIDATION = newsoup.find(id="__EVENTVALIDATION")['value']
        TSM_HiddenField = newsoup.find(id="_TSM_HiddenField_")['value']
        xls_url = "https://myaccount.sfwater.org/~~~QUFBQUFBVzA4aEozRlhFbUNRa1VITUYrdE9lOEtFSnRCMFN1U1NKK25wcTg4TGluOHc9PQ==ZZZ"

        # Populate data request POST
        xls_data = {"__VIEWSTATE":VIEWSTATE,
            "__VIEWSTATEGENERATOR":VIEWSTATEGENERATOR,
            "__EVENTVALIDATION":EVENTVALIDATION,
            "_TSM_HiddenField_":TSM_HiddenField,
            "SD":start_day,
            "tb_DAILY_USE":"Daily Use",
            "dl_UOM":"GALLONS",
            "img_EXCEL_DOWNLOAD_IMAGE.x":"12",
            "img_EXCEL_DOWNLOAD_IMAGE.y":"11",
            "ED":end_day}

        xls_file = c.post(xls_url, data = xls_data, 
            headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"})
        usage_list = xls_file.content.split("\n")
        
        # Pop off first line, reading: "Date   Consumption in GALLONS"
        usage_list.pop(0) 
        
        return usage_list

if __name__ == "__main__":

    arguments = docopt(__doc__)
    
    if arguments['--version']:
        print "%s v. %s" % (__title__, __version__)
        sys.exit()
    
    mode = output_mode(arguments)
    start_datetime, end_datetime = init(arguments)
    userid, password = get_credentials()

    try:
        water = water_usage(userid, password, start_datetime, end_datetime)
    except ValueError:
        loginerror()
    else:
        output(water, mode, start_datetime, end_datetime)




