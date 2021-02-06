import argparse
import traceback
import time
from db import Session
from functions import check_date, update_price_and_balance_data, get_price_and_balance_date, get_forex_data
from datetime import datetime, date, timedelta
from constants import currency


def mode_loop(args):
    while True:
        try:
            _ = update_price_and_balance_data(session)
            session.commit()
            print(f' {datetime.now().strftime("%H:%M:%S")}  Next update in {args.interval} minutes...')
            time.sleep(args.interval * 60)
    
        except KeyboardInterrupt:
            break    

    
def mode_update(args):        
    log_str = update_price_and_balance_data(session, test=args.test)
    session.commit()
    print(f' {log_str}')


def mode_show(args):
    today = date.today()
    since_date = today - timedelta(days=args.since)

    from_date = check_date(args.date_from) if args.date_from else None

    if not from_date:
        from_date = since_date

    to_date = check_date(args.date_to) if args.date_to else None

    if not to_date:
        to_date = today

    if from_date > today or from_date > to_date:
        msg = 'in the future' if from_date > today else f'beyond "to" date "{to_date}"'
        print(f' invalid "from" date ({msg}) "{from_date}" - correcting to the last 7 days')
        from_date = since_date
        to_date = today

    to_date = to_date + timedelta(days=1)
    date_range = [from_date + timedelta(days=x) for x in range((to_date-from_date).days)]
    data_by_date = get_price_and_balance_date(session, date_range)

    if not data_by_date:
        exit()

    fiat_currency = (args.currency or currency).upper()

    if fiat_currency != 'USD':
        forex_data = get_forex_data(date_range=sorted(list(data_by_date.keys())), currency=fiat_currency)

    total_earned_in_eth = 0
    total_earned_in_fiat = 0

    title_str = f'date           ETH earned      ETH price   {fiat_currency:>4} earned'
    print(f'\n {title_str}\n {len(title_str) * "="}')
    for date_ in data_by_date:
        day_data = data_by_date[date_]
        day_eth_earnings = sum([day_data.validators[v].earned_eth for v in day_data.validators])
        price_of_one_in_fiat = day_data.price.display

        if fiat_currency != 'USD':
            price_of_one_in_fiat *= forex_data[date_.strftime('%Y-%m-%d')]

        day_eth_earnings_in_fiat = day_eth_earnings * price_of_one_in_fiat

        f_day_eth_earnings = f'{day_eth_earnings:.4f} ETH'
        f_day_eth_price_in_fiat = f'{price_of_one_in_fiat:,.2f} {fiat_currency}'
        f_day_eth_earnings_in_fiat = f'{day_eth_earnings_in_fiat:,.2f} {fiat_currency}'
        print(
            f' {date_.strftime("%Y/%m/%d")}   {f_day_eth_earnings:>12}   '
            f'{f_day_eth_price_in_fiat:>12}  {f_day_eth_earnings_in_fiat:>12}'
        )

        total_earned_in_eth += day_eth_earnings
        total_earned_in_fiat += day_eth_earnings_in_fiat

    f_total_earned_in_eth = f'{total_earned_in_eth:.4f} ETH'
    f_total_earned_in_fiat = f'{total_earned_in_fiat:,.2f} {fiat_currency}'

    footer_str = f'             {f_total_earned_in_eth:>12}                 {f_total_earned_in_fiat:>12}'
    print(f' {len(title_str) * "="}\n {footer_str}')

    print()


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
        '-d', '--detailed-view', action='store', type=int, help='show extra details (eg separate validator earnings)'
    )

    parser_loop.set_defaults(func=mode_loop)
    parser_update.set_defaults(func=mode_update)
    parser_show.set_defaults(func=mode_show)

    args = parser.parse_args()

    session = Session()

    try:
        args.func(args)

    except AttributeError as e:
        traceback.print_exc()
        parser.print_help()

    finally:
        session.close()
