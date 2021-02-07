
Eth2 Daily Tracker
===================
This is a Python (3.7+) tool to help you keep track of how much Ether you earn via staking (along with the price of ETH and so the fiat value of your staking rewards) on a day-to-day basis. 

The idea behind the application is that it needs to be run regularly to pick up ETH price changes throughout the day. In theory you could run it at 00:02 and 23:58 to pick up the staking rewards for the day.

Installation
============
Extract the files into their own folder and either install `sqlalchemy` and `requests` yourself or run `pip/pip3 install -r requirements txt`. Run `python/python3 eth2_daily_tracker.py -h` from a CLI environment (Command Prompt or PowerShell in Windows or any Linux terminal) to see the modes of operation.

Modes of operation
==================
`eth2_daily_tracker.py loop` or `eth2_daily_tracker.py l` - Update the saved data every x minutes (default: 5). Use this mode if you want to run the script in a terminal demultiplexer like tmux or screen.

`eth2_daily_tracker.py update` or `eth2_daily_tracker.py u` - Update the saved data once and then exit. Use this mode if you want to run the script via crontab or a task scheduler or just to run it from the command line.

`eth2_daily_tracker.py show` or `eth2_daily_tracker.py s` - Generate a report to display the saved data. The default period is the last week but you can alter this with `--date-from`/`--date-to` (to go for a historical range) args or `--since` (the number of days ago you want to start the range from).

A log file, `updates.log`, is generated in the directory from which you are running the app - if you're running via crontab you can check this log file to make sure it's still updating.

The config.ini file
===================
This is generated when you first run the script. You need a CoinMarketCap API key. To obtain one, go to https://pro.coinmarketcap.com/ and then paste it in when asked. 

You also need to either know the index/es of your validator(s) or the eth1 address (0x...) of the wallet you used to send the deposits to create your validators.

The default currency is USD (all ETH prices are saved in it in the database) but you can specify a different currency to display the ETH price and daily earnings in the config file or (more temporarily) by running the `show` mode with `-c/--currency` followed by the symbol (eg EUR) of your choice. This is a bit ropey as the datasource for these forex rates doesn't update them over the weekend (because *their* datasource doesn't update them over the weekend) so Sunday's rate will be the same as Friday's. It's enough for ball park figures.

To do
=====
- Add support for exporting to CSV