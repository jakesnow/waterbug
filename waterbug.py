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
import sys
import getpass
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from docopt import docopt

from termgraph import main as graph

__title__ = 'waterbug'
__version__ = '0.1'
__author__ = 'Jake Snow'
__license__ = 'MIT'
__copyright__ = 'Copyright 2016 Jacob A. Snow'


def get_credentials():
    '''
    If credentials are hard-coded constants, return them.  Otherwise
    prompt the user.
    '''
    try:
        login = USERID
    except NameError:
        login = raw_input("Please enter your SF Water login: ")
    try:
        passw = PASSWORD
    except NameError:
        passw = getpass.getpass("Please enter your SF Water password: ")
    return (login, passw)


def loginerror():
    '''Print formatted login-error notification'''
    print "\n====================================="
    print "Your login or password was incorrect."
    print "====================================="


def datetime_to_day(date_time):
    '''convert datetime object to string of the form "MM/DD/YYYY'''
    day = "%s/%s/%s" % (date_time.month, date_time.day, date_time.year)
    return day


def fix_future_date(date_time):
    '''If date_time is in the future, move it to previous year.'''
    if date_time > datetime.today():
        previous_year = date_time - relativedelta(years=1)
        return previous_year
    else:
        return date_time


def output_mode(args):
    '''Identify login mode from args dictionary.'''
    if args['--graph']:
        return "graph"
    elif args['--xls']:
        return "xls"
    else:
        return "text"


def terminal_output_header(start, end):
    '''Print header for terminal output.'''
    print "\nWater Use in Gallons, %s through %s:" % (start, end)
    print "======================================================"


def render_output(water_use, output, start_date, end_date):
    '''Output to terminal (text or termgraph) or xls depending on output mode.'''
    start = datetime_to_day(start_date)
    end = datetime_to_day(end_date)
    if output == "text":
        terminal_output_header(start, end)
        for day_use_pair in water_use:
            print day_use_pair
    elif output == "graph":
        terminal_output_header(start, end)
        graph(water_use)
    elif output == "xls":
        xls_file = "Date\tConsumption in GALLONS\n"
        for day_use_pair in water_use:
            xls_file += day_use_pair + "\n"
        write_xls = open("water_usage.xls", 'wb')
        write_xls.write(xls_file.encode("utf-8"))
        write_xls.close()


def get_daterange(arguments):
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

    with requests.Session() as session:

        waterbill_url = "https://myaccount.sfwater.org/~~~QUFBQUFBV1ZFb1Evbm1zMEpWSzRCMmYrcEZtT05zMkpJMHdEM2VqQnNPTlpEUjFlR2c9PQ==ZZZ"
        response = session.get("https://myaccount.sfwater.org")

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract values from page that must be in the login POST
        viewstate_login = soup.find(id="__VIEWSTATE")['value']
        viewstategenerator_login = soup.find(
            id="__VIEWSTATEGENERATOR")['value']
        eventvalidation_login = soup.find(id="__EVENTVALIDATION")['value']

        # Populate login POST
        login_data = {"__VIEWSTATE": viewstate_login,
                      "__VIEWSTATEGENERATOR": viewstategenerator_login,
                      "__EVENTVALIDATION": eventvalidation_login,
                      "tb_USER_ID": userid,
                      "tb_USER_PSWD": password,
                      "btn_SIGN_IN_BUTTON": "Sign in"}

        # Submit login
        login = session.post(waterbill_url, data=login_data)

        # Raise exception if login credentals fail
        if "<h2>Sign In Failure</h2>" in login.content:
            loginerror()
            sys.exit()

        account_url = "https://myaccount.sfwater.org/~~~QUFBQUFBV3RCUW5sMFltOXVXNGtBUVBKVVhRQkRxVGFmU2JRVGVBbGJ0Z2tWWkNRRFE9PQ==ZZZ"
        my_account = session.get(account_url)

        # print my_account.content

        newsoup = BeautifulSoup(my_account.content, "html.parser")

        # Extract values from page that must be in the data-request POST
        viewstate_data = newsoup.find(id="__VIEWSTATE")['value']
        viewstategenerator_data = newsoup.find(
            id="__VIEWSTATEGENERATOR")['value']
        eventvalidation_data = newsoup.find(id="__EVENTVALIDATION")['value']
        tsm_hiddenfield = newsoup.find(id="_TSM_HiddenField_")['value']

        xls_url = "https://myaccount.sfwater.org/~~~QUFBQUFBVzA4aEozRlhFbUNRa1VITUYrdE9lOEtFSnRCMFN1U1NKK25wcTg4TGluOHc9PQ==ZZZ"

        # Populate data request POST
        xls_data = {"__VIEWSTATE": viewstate_data,
                    "__VIEWSTATEGENERATOR": viewstategenerator_data,
                    "__EVENTVALIDATION": eventvalidation_data,
                    "_TSM_HiddenField_": tsm_hiddenfield,
                    "SD": start_day,
                    "tb_DAILY_USE": "Daily Use",
                    "dl_UOM": "GALLONS",
                    "img_EXCEL_DOWNLOAD_IMAGE.x": "12",
                    "img_EXCEL_DOWNLOAD_IMAGE.y": "11",
                    "ED": end_day}

        xls_file = session.post(
            xls_url,
            data=xls_data,
            headers={"Accept": "text/html,application/xhtml+xml,application\
                        /xml;q=0.9,image/webp,*/*;q=0.8"})

        usage_list = xls_file.content.split("\n")
        # Pop off first line, reading: "Date   Consumption in GALLONS"
        usage_list.pop(0)

        return usage_list


def return_version(args):
    '''If user requests version, return version and exit.'''
    if args['--version']:
        print "%s v. %s" % (__title__, __version__)
        sys.exit()


def main(args):
    '''Collect and return requested water-usage data.'''

    mode = output_mode(args)
    start_datetime, end_datetime = get_daterange(args)
    userid, password = get_credentials()

    water = water_usage(userid, password, start_datetime, end_datetime)
    render_output(water, mode, start_datetime, end_datetime)

if __name__ == "__main__":

    # USERID = "[SF WATER USERNAME]"
    # PASSWORD = "[SF WATER PASSWORD]"

    ARGUMENTS = docopt(__doc__)
    return_version(ARGUMENTS)
    main(ARGUMENTS)
