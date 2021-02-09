import time
from datetime import datetime, date, timedelta
from functions import (
    update_price_and_balance_data, check_date, get_price_and_balance_data, get_forex_data,
    DayData, print_detailed_day, print_non_detailed_day
)

from constants import currency, validator_indexes


# def mode_loop(args, session):
#     while True:
#         try:
#             update_price_and_balance_data(session, loop=True)
#             print(f' {datetime.now().strftime("%H:%M:%S")}  Next update in {args.interval} minutes...')
#             time.sleep(args.interval * 60)
#
#         except KeyboardInterrupt:
#             break


def mode_update(args, session):
    if args.loop:
        while True:
            try:
                update_price_and_balance_data(session, loop=True)
                print(f' {datetime.now().strftime("%H:%M:%S")}  Next update in {args.interval} minutes...')
                time.sleep(args.interval * 60)

            except KeyboardInterrupt:
                break

    else:
        update_price_and_balance_data(session, use_local_data=args.test, run_as_task=args.scheduled)


def mode_show(args, session):
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
    date_range = [from_date + timedelta(days=x) for x in range((to_date - from_date).days)]
    data_by_date = get_price_and_balance_data(session, date_range)

    more_than_1_validator = False

    for date_ in data_by_date:
        if len(data_by_date[date_].validators) > 1:
            more_than_1_validator = True
            break

    if not data_by_date:
        exit()

    fiat_currency = (args.currency or currency).upper()

    if fiat_currency == 'USD':
        forex_data = None

    else:
        forex_data = get_forex_data(date_range=sorted(list(data_by_date.keys())), currency=fiat_currency)

    total_earned_in_eth = 0
    total_earned_in_fiat = 0

    show_validators = True if args.detailed_view and more_than_1_validator else False

    title_str = (
        f'date       {" index" if show_validators else ""}   ETH earned      ETH price   {fiat_currency:>4} earned'
    )
    print(f'\n {title_str}\n {len(title_str) * "="}')

    first_date = True
    for day_date in data_by_date:
        date_str = day_date.strftime("%Y/%m/%d")
        day_data = data_by_date[day_date]
        price_of_one_in_fiat = day_data.price.display

        if fiat_currency != 'USD':
            price_of_one_in_fiat *= forex_data[day_date.strftime('%Y-%m-%d')]

        day_eth_earnings = sum([day_data.validators[v].earned_eth for v in day_data.validators])
        day_totals = DayData(
            eth_earned=day_eth_earnings, fiat_price_of_1=price_of_one_in_fiat, fiat_currency=fiat_currency
        )

        if args.detailed_view:
            for val_idx in sorted(validator_indexes, key=int):
                try:
                    validator = day_data.validators[val_idx]

                except KeyError:
                    pass

                else:
                    day_totals.validators[val_idx] = DayData(
                        validator.earned_eth, fiat_price_of_1=price_of_one_in_fiat, fiat_currency=fiat_currency
                    )

        if show_validators:
            if not first_date:
                print(f' {len(title_str) * "-"}')

            print_detailed_day(date_str, day_totals)

            first_date = False

        else:
            print_non_detailed_day(date_str, day_totals)

        total_earned_in_eth += day_eth_earnings
        total_earned_in_fiat += day_totals.fiat_price_of_earned

    f_total_earned_in_eth = f'{total_earned_in_eth:.4f} ETH'
    f_total_earned_in_fiat = f'{total_earned_in_fiat:,.2f} {fiat_currency}'

    footer_str = (
        f'          {"      " if show_validators else ""}  '
        f'{f_total_earned_in_eth:>12}                 {f_total_earned_in_fiat:>12}'
    )

    print(f' {len(title_str) * "="}\n {footer_str}')

    print()
