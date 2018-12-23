import os
from os.path import expanduser
from urllib.request import urlopen
import pandas as pd
import logging
import datetime as dt

DEFAULT_ERES_DIRECTORY=os.path.join(expanduser('~/.eres'))
base_directory = DEFAULT_ERES_DIRECTORY

def fill_missing_values(df_funds):
    df_funds = df_funds.groupby(['dt', 'fund_id']).first()['price'].sort_index() \
            .unstack(level=-1) \
            .fillna(method='ffill') \
            .stack() \
            .reset_index() \
            .rename(columns={0: 'price'})
    return df_funds

def download_fund(fund_id, force=False):

    fname = get_fname_for_fund(fund_id)
    mtime = os.stat(fname).st_mtime
    last_refresh = dt.datetime.fromtimestamp(mtime)

    if not force and \
        dt.datetime.now() - last_refresh < dt.timedelta(0, 12):
        logging.debug('No refresh required for fund_id[%d], last refresh[%s]' \
                        % (fund_id, str(last_refresh)))
        return

    url = 'https://www.eres-group.com/eres/export.php?idFond=%d&format=CSV' \
            % fund_id
    response = urlopen(url)
    csv = response.read()

    fp = open(fname, 'w')
    fp.write(csv.decode())
    logging.info('writing %s' % fname)


def load_fund(fund_id):

    fname = get_fname_for_fund(fund_id)

    return pd.read_csv(fname,
                       names=['fund_id', 'fund_name', 'dt', 'price'],
                       delimiter=';',
                       parse_dates=['dt'])

def load_funds(fund_ids):
    l = []
    for fund_id in fund_ids:
        df_fund = load_fund(fund_id)
        l.append(df_fund)
    return fill_missing_values(pd.concat(l))


def load_positions(portfolio):
    fname = get_fname_for_positions(portfolio)
    return pd.read_csv(fname)

def get_fname_for_fund(fund_id):
    return os.path.join(base_directory, '%d.csv' % fund_id)

def get_fname_for_valo(portfolio):
    return os.path.join(base_directory,
                        'portfolios',
                        portfolio,
                        'valo.csv')


def get_fname_for_positions(portfolio):
    return os.path.join(base_directory,
                        'portfolios',
                        portfolio,
                        'positions.csv')

def write_valo(portfolio, df_valo):

    fname = get_fname_for_valo(portfolio)

    df_valo.to_csv(fname)

def list_portfolios(directory):

    ret = []
    root_dir = os.path.join(base_directory,
                            'portfolios')

    for entry in os.listdir(root_dir):
        fpath = os.path.join(root_dir,
                             entry)
        if os.path.isdir(fpath):
            ret.append((entry, fpath))

    return pd.DataFrame(ret, columns=['name', 'path'])
