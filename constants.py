from pathlib import Path
import configparser
import requests

debug = False

source_path = Path(__file__).parent
data_path = source_path / 'data'
data_path.mkdir(exist_ok=True)
config_file = source_path / 'config.ini'
log_file = source_path / 'updates.log'
db_file = data_path / 'data.db'
cmc_json_file = data_path / 'cmc_data.json'
bc_json_file = data_path / 'bc_data.json'


def api_key_test(api_key):
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': api_key}
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info'
    parameters = {'slug': 'bitcoin'}
    cmc_data = requests.get(url, headers=headers, params=parameters).json()

    return cmc_data['status']


def get_validators_from_eth1_address(eth1_address):
    url = f'https://beaconcha.in/api/v1/validator/eth1/{eth1_address}'
    response = requests.get(url)
    if response.status_code == 200:
        validators = [str(v['validatorindex']) for v in response.json()['data']]

        return validators

    return None


cfg = configparser.RawConfigParser()

if not config_file.is_file():
    cfg['coinmarketcap api'] = {}
    cfg['validator indexes'] = {}
    cfg['options'] = {}

    print(
        '\n You need a CoinMarketCap API key in order to use this application. '
        'Goto https://pro.coinmarketcap.com/ if you need to create one.\n'
    )

    while True:
        api_key = input(' Enter your CoinMarketCap API key: ')
        status = api_key_test(api_key)

        if status['error_code'] == 0:
            print(' Connected successfully.')
            break

        print(f' Invalid API key: {api_key}')

    cfg['coinmarketcap api']['api key'] = api_key

    print(
        '\n You need to add the indexes of your validators. Either enter the indexes, '
        'separated by spaces or commas, or enter the address of'
    )

    indexes = input(' the eth1 wallet ("0x...") you used to make the deposits: ')

    if len(indexes) == 42 and indexes.startswith('0x'):
        val_indexes_list = get_validators_from_eth1_address(indexes)

    else:
        val_indexes_list = [v.strip() for v in indexes.split(',')]

    val_indexes = []
    if val_indexes_list:
        for v_idx in sorted(val_indexes_list):
            try:
                v = int(v_idx)

            except ValueError:
                print(f' Invalid validator index: {v_idx}')

            else:
                print(f' Added validator index: {v_idx}')
                val_indexes.append(str(v_idx))

    if not val_indexes:
        print('\n No valid validator indexes found.\n')
        exit()

    cfg['validator indexes']['validators'] = ', '.join(val_indexes)
    cfg['options']['currency'] = 'USD'

    with config_file.open('w') as f:
        cfg.write(f)

    print(f'\n Config saved with default values. Open "{config_file}" to make changes.\n')

cfg.read(config_file)

api_key = cfg['coinmarketcap api'].get('api key', fallback=None)
currency = cfg['options'].get('currency', 'USD')
validator_indexes = [v.strip() for v in cfg['validator indexes'].get('validators').split(',')]

if not api_key:
    print(' No CoinMarketCap API key found.')
    exit()

cmc_headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': api_key}

# choose between start, end, high or low
eth_price_to_use = 'high'
