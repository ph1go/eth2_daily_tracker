import json
import time
import requests
from datetime import datetime, date, timedelta
from dataclasses import dataclass, InitVar, field
from typing import Dict
from constants import eth_price_to_use, bc_json_file, cmc_json_file, log_file, num_pad, debug, cmc_headers, validator_indexes
from db import Price, validators, ValidatorMixin


@dataclass
class PriceDc:
    start: float = field(init=False)
    high: float = field(init=False)
    low: float = field(init=False)
    end: float = field(init=False)

    price: InitVar[Price] = None

    def __post_init__(self, price):
        self.start = price.start
        self.high = price.high
        self.low = price.low
        self.end = price.end

    @property
    def display(self):
        try:
            price_to_use = getattr(self, eth_price_to_use)

        except AttributeError:
            print(f' Invalid price type: "{eth_price_to_use}" - choose from "start", "end", "high" or "low"')
            price_to_use = self.low

        return price_to_use


@dataclass
class ValidatorDc:
    start: int = field(init=False)
    end: int = field(init=False)
    earned_gwei: int = field(init=False)
    earned_eth: float = field(init=False)

    validator: InitVar[ValidatorMixin] = None

    def __post_init__(self, validator):
        self.start = validator.start
        self.end = validator.end
        self.earned_gwei = self.end - self.start if self.end else 0
        self.earned_eth = self.earned_gwei / 1000000000


@dataclass
class Day:
    date: date
    price: PriceDc
    validators: Dict[str, ValidatorDc] = field(init=False, default_factory=dict)


@dataclass
class DayData:
    eth_earned: float
    fiat_price_of_1: float
    fiat_price_of_earned: float = field(init=False)
    eth_earned_str: str = field(init=False)
    fiat_price_of_1_str: str = field(init=False)
    fiat_price_of_earned_str: str = field(init=False)

    fiat_currency: InitVar[str] = None
    validators: Dict[str, 'DayData'] = field(default_factory=dict)

    def __post_init__(self, fiat_currency: str):
        self.fiat_price_of_earned = self.eth_earned * self.fiat_price_of_1
        self.eth_earned_str = f'{self.eth_earned:.4f} ETH'
        self.fiat_price_of_1_str = f'{self.fiat_price_of_1:,.2f} {fiat_currency}'
        self.fiat_price_of_earned_str = f'{self.fiat_price_of_earned:,.2f} {fiat_currency}'


def update_price_and_balance_data(session, test=False, loop=False):
    current_eth_price = get_current_eth_price(test=test)
    current_validator_balances = get_validator_balances(test=test)

    today = date.today()
    yesterday = today - timedelta(days=1)

    today_price = session.query(Price).filter(Price.date == today).first()

    if today_price:
        today_price.update_prices(current_eth_price)

    else:
        yesterday_price = session.query(Price).filter(Price.date == yesterday).first()

        if yesterday_price:
            yesterday_price.update_prices(current_eth_price)

        today_price = Price(date=today, price=current_eth_price)
        session.add(today_price)

    for val_idx in validators:
        Validator = validators[val_idx]
        today_balance = session.query(Validator).filter(Validator.date == today).first()

        if today_balance:
            today_balance.end = current_validator_balances[val_idx]

        else:
            yesterday_balance = session.query(Validator).filter(Validator.date == yesterday).first()

            if yesterday_balance:
                yesterday_balance.end = current_validator_balances[val_idx]

            today_balance = Validator(date=today, start=current_validator_balances[val_idx])
            session.add(today_balance)

    log_str = (
        f'{datetime.now().strftime("%Y/%m/%d %H:%M")}  '
        f'Updated successfully (current ETH price: {current_eth_price:,.2f} USD)'
    )

    with log_file.open('a') as f:
        f.write(f'{log_str}\n')

    if not loop:
        print(f' {log_str}')

    session.commit()


def get_forex_data(date_range, currency):
    start_date = min(date_range)
    if start_date.weekday() > 4:
        start_date = start_date - timedelta(days=start_date.weekday() - 4)

    start_date = start_date.strftime('%Y-%m-%d')
    end_date = max(date_range).strftime('%Y-%m-%d')

    url = 'https://api.exchangeratesapi.io/'

    if start_date == end_date:
        url += f'{start_date}?base=USD&symbols={currency}'

    else:
        url += f'history?start_at={start_date}&end_at={end_date}&symbols={currency}&base=USD'

    response = requests.get(url).json()

    if response.get('error'):
        print(f' Invalid currency symbol: {currency}')
        exit()

    data = {}
    if start_date == end_date:
        data[date_range[0]] = response['rates'][currency]

    else:
        for d in date_range:
            date_ = d.strftime('%Y-%m-%d')
            while True:
                day_data = response['rates'].get(d.strftime('%Y-%m-%d'))
                if day_data:
                    break

                d -= timedelta(days=1)

            data[date_] = day_data['EUR'] if day_data else None

    return data


def get_price_and_balance_date(session, date_range):
    results = {}
    for date_ in date_range:
        date_price = session.query(Price).filter(Price.date == date_).first()

        if date_price:
            results[date_] = Day(date=date_, price=PriceDc(date_price))

            for val_idx in validators:
                validator = validators[val_idx]

                date_balance = session.query(validator).filter(validator.date == date_).first()

                if date_balance:
                    results[date_].validators[val_idx] = ValidatorDc(date_balance)

    return results


def check_date(in_date):
    return_date = None
    if len(in_date) in [6, 8]:
        try:
            return_date = datetime.strptime(in_date, '%y%m%d' if len(in_date) == 6 else '%Y%m%d').date()

        except ValueError:
            pass

    if not return_date:
        print(f' Check date string "{in_date}"')

    return return_date


def get_current_eth_price(test=False):
    if test:
        with cmc_json_file.open() as f:
            cmc_data = json.load(f)

    else:
        if debug:
            print(f' {time.strftime("%H:%M:%S")} downloading coinmarketcap data... ', end='', flush=True)
            c_start = time.perf_counter()

        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
        cmc_data = requests.get(url, headers=cmc_headers, params={'id': '1027'}).json()

        with cmc_json_file.open('w') as f:
            json.dump(cmc_data, f)

    try:
        return cmc_data['data']['1027']['quote']['USD']['price']

    except Exception as e:
        print(e)
        return None


def get_validator_balances(test=False):
    if test:
        with bc_json_file.open() as f:
            bc_response = json.load(f)

    else:
        url = f'https://beaconcha.in/api/v1/validator/{",".join(validator_indexes)}'
        bc_response = requests.get(url).json()

        with bc_json_file.open('w') as f:
            json.dump(bc_response, f)

    _ = bc_response['data']
    data = _ if isinstance(_, list) else [_]

    return {str(v['validatorindex']): v['balance'] for v in data}


def print_detailed_day(date_str, day_totals):
    print(
        f' {date_str}  total {day_totals.eth_earned_str:>{num_pad}}   {day_totals.fiat_price_of_1_str:>{num_pad}}  '
        f'{day_totals.fiat_price_of_earned_str:>{num_pad}}'
    )

    for val_idx in day_totals.validators:
        validator = day_totals.validators[val_idx]
        print(
            f' {" ":>10} {val_idx:>6} {validator.eth_earned_str:>{num_pad}}   '
            f'{" ":>{num_pad}}  '
            f'{validator.fiat_price_of_earned_str:>{num_pad}}'
        )


def print_non_detailed_day(date_str, day_totals):
    print(
        f' {date_str}  {day_totals.eth_earned_str:>{num_pad}}   {day_totals.fiat_price_of_1_str:>{num_pad}}  '
        f'{day_totals.fiat_price_of_earned_str:>{num_pad}}'
    )
