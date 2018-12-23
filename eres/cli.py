import argparse
from os.path import expanduser
import eres.helpers as hpl
import pandas as pd
import os
import logging
import sys


logging.basicConfig(level=logging.DEBUG)

#def get_filename_for_portfolio(portfolio,
#                               directory):
#    return os.path.join(directory,
#                        'portfolios',
#                        portfolio,
#                        'positions.csv')

def refresh_cache(fund_ids,
                  directory):
    for fund_id in fund_ids:
        hpl.download_fund(fund_id, directory)



def refresh_fund_cache(portfolios):
	for portfolio in portfolios:
		fname = get_fname_for_portfolio(portfolio)
		positions = pd.read_csv(fname)
		fund_ids = positions['fund_id'].unique()
		print("fund_ids:", fund_ids)

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
                        help='Show current positions in the porfolio')
    parser.add_argument('--cache-directory',
                        default=expanduser('~/.eres'))
    parser.add_argument('--portfolio',
                        default=None)

    args = parser.parse_args()

    portfolios = hpl.list_portfolios(args.cache_directory)

    refresh_cache = args.refresh_cache

    if refresh_cache:
        logging.info("Refreshing cache")
        fund_ids = []
        for portfolio in portfolios:
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

    df_positions = hpl.load_positions(portfolio)

    if args.show_positions:
        print(df_positions.to_string())
        sys.exit(0)

    df_funds = hpl.load_funds(df_positions['fund_id'].unique())

    # merge with positions
    df = df_funds.merge(df_positions)

    df['valo'] = df['price'] * df['equities']
    df_valo = df.groupby('dt').sum()[['valo']]

    for lag in [1, 30, 180]:
        df_valo['%dd_net' % lag] = df_valo['valo'] - df_valo['valo'].shift(lag)
        df_valo['%dd_ratio' % lag] = 100. * df_valo['%dd_net' % lag] / df_valo['valo'].shift(lag)

    print(df_valo.tail(30).to_string())

    hpl.write_valo(portfolio, df_valo)

