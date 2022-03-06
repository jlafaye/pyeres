import os
from os.path import expanduser
from urllib.request import urlopen
import pandas as pd
import logging
import datetime as dt
import numpy as np

DEFAULT_ERES_DIRECTORY=os.path.join(expanduser('~/.eres'))
base_directory = DEFAULT_ERES_DIRECTORY


def fill_missing_values(df_funds):
    df_funds = df_funds.groupby(['date', 'fund_id']).first()['price'].sort_index() \
            .unstack(level=-1) \
            .fillna(method='ffill') \
            .stack() \
            .reset_index() \
            .rename(columns={0: 'price'})
    return df_funds


def expand_to_daily(df, date_column, key_columns):
    df = (
        df
        .set_index([date_column] + key_columns)
        .sort_index()
        .unstack()
    )
    # we add a date in the future to interpolate from
    # the last date available to yesterday
    df.loc[dt.datetime.now()] = np.nan
    return (df.resample('1d')
              .ffill()
              .stack()
              .reset_index())


def download_fund(fund_id, force=False):
    fname = get_fname_for_fund(fund_id)
    if os.path.exists(fname):
        mtime = os.stat(fname).st_mtime
        last_refresh = dt.datetime.fromtimestamp(mtime)
    else:
        last_refresh = None

    if last_refresh is not None and not force and \
            dt.datetime.now() - last_refresh < dt.timedelta(0, 12):
        logging.debug('No refresh required for fund_id[%d], last refresh[%s]' \
                        % (fund_id, str(last_refresh)))
        return

    url = f"https://www.eres-group.com/eres/new_fiche_json.php?id={fund_id}"
    logging.info(f'Downloading {url}')
    response = urlopen(url)
    data = response.read().decode()

    with open(fname, 'w') as fp:
        fp.write(data)
        logging.info('writing %s' % fname)


def load_fund(fund_id):
    fname = get_fname_for_fund(fund_id)

    df = (
        pd
        .read_json(fname) #, parse_dates=['d'])
        .rename(columns={
            'd': 'date',
            'p': 'price'
        })
    )
    df['fund_id'] = fund_id
    df['fund_name'] = f'{fund_id}' 
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    return df

    return pd.read_csv(fname,
                       names=['fund_id', 'fund_name', 'date', 'price'],
                       delimiter=';',
                       parse_dates=['date'])

def load_funds(fund_ids):
    l = []
    for fund_id in fund_ids:
        df_fund = load_fund(fund_id)
        l.append(df_fund)
    return fill_missing_values(pd.concat(l))


def load_positions(portfolio):
    fname = get_fname_for_positions(portfolio)
    df = pd.read_csv(fname, parse_dates=['date'])
    return df


def get_fname_for_fund(fund_id):
    return os.path.join(base_directory, f'{fund_id}.json')


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
