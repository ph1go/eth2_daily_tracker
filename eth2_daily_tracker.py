#!/usr/bin/python

import argparse
import traceback
from modes import mode_show, mode_loop, mode_update
from db import Session

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()
    parser_loop = subparsers.add_parser(
        'loop', aliases=['l'], help=(
            'update price and balance data until stopped, repeating every <interval> minutes - use this mode '
            'if you want to run the application in a terminal demultiplexer (eg: screen or tmux)'
        )
    )

    parser_update = subparsers.add_parser(
        'update', aliases=['u'], help=(
            'update price and balance data once - use this mode if you want to control the timing via crontab '
            'or a task scheduler'
        )
    )

    parser_update.add_argument(
        '-t', '--test', action='store_true',
        help='use locally saved data instead of getting it fresh from the apis (saves api calls while testing)'
    )

    parser_loop.add_argument(
        '-i', '--interval', action='store', type=int, default=5,
        help='the time to wait in minutes between updates (default: 5)'
    )

    parser_show = subparsers.add_parser('show', help='display price and balance data', aliases=['s'])

    parser_show.add_argument(
        '-c', '--currency', action='store', type=str,
        help='show prices in particular currency - change the default in config.ini'
    )

    parser_show.add_argument(
        '-df', '--date-from', action='store', type=str,
        help='the date ("YYYYMMDD" or "YYMMDD") from which to display prices/balances'
    )

    parser_show.add_argument(
        '-dt', '--date-to', action='store', type=str,
        help='the date ("YYYYMMDD" or "YYMMDD") to which to display prices/balances'
    )

    parser_show.add_argument(
        '-s', '--since', action='store', type=int, default=7,
        help='display prices/balance since x days ago (default: 7)'
    )

    parser_show.add_argument(
        '-d', '--detailed-view', action='store_true', help='show extra details (eg separate validator earnings)'
    )

    parser_loop.set_defaults(func=mode_loop)
    parser_update.set_defaults(func=mode_update)
    parser_show.set_defaults(func=mode_show)

    args = parser.parse_args()

    session = Session()

    try:
        args.func(args, session)

    except AttributeError as e:
        traceback.print_exc()
        parser.print_help()

    finally:
        session.close()
