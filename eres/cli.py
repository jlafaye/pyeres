import argparse
from os.path import expanduser
import eres.helpers as hpl
import pandas as pd
import logging
import sys


logging.basicConfig(level=logging.DEBUG)


def run():

    parser = argparse.ArgumentParser(description='Eres command line tool')
    parser.add_argument('--refresh-cache',
                        action='store_true',
                        default=False)
    parser.add_argument('--show-portfolios',
                        action='store_true',
                        help='Show portfolios')
    parser.add_argument('--show-positions',
                        action='store_true',
                        default=False,
                        help='Show current positions in the porfolio')
    parser.add_argument('--cache-directory',
                        default=expanduser('~/.eres'))
    parser.add_argument('--portfolio',
                        default=None)

    args = parser.parse_args()

    portfolios = hpl.list_portfolios(args.cache_directory)

    if args.refresh_cache:
        logging.info("Refreshing cache")
        fund_ids = []
        for portfolio in portfolios['name'].unique():
            positions = hpl.load_positions(portfolio)
            fund_ids += list(positions['fund_id'].unique())
        fund_ids = list(set(fund_ids))
        for fund_id in fund_ids:
            hpl.download_fund(fund_id)

    if args.show_portfolios:
        print('Available portfolio(s):')
        print(portfolios.to_string())
        sys.exit(0)

    portfolio = portfolios['name'].values[0] if not args.portfolio else args.portfolio
    print('Selected portfolio: {}'.format(portfolio))

    positions = hpl.load_positions(portfolio)
    daily_positions = hpl.expand_to_daily(positions, 'date', ['fund_id'])

    if args.show_positions:
        print('Positions')
        print(positions.to_string())
        sys.exit(0)

    funds = hpl.load_funds(positions['fund_id'].unique())
    daily_funds = hpl.expand_to_daily(funds, 'date', ['fund_id'])

    # merge funds + positions into a single huge
    # dataframe with one row per day
    df = daily_positions.merge(daily_funds)
    df['volume'] = df['price'] * df['equities']

    valo = pd.DataFrame({'valo': df.groupby('date')['volume'].sum()})

    for lag in [1, 30, 180, 360]:
        valo['%dd_net' % lag] = valo['valo'] - valo['valo'].shift(lag)
        valo['%dd_ratio' % lag] = 100. * valo['%dd_net' % lag] / valo['valo'].shift(lag)

    print(valo.tail(30).to_string())

    hpl.write_valo(portfolio, valo)

