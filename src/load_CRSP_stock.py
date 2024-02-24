from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path

import numpy as np
import pandas as pd
import wrds

import config

DATA_DIR = Path(config.DATA_DIR)
WRDS_USERNAME = config.WRDS_USERNAME
START_DATE = config.START_DATE
END_DATE = config.END_DATE



def pull_CRSP_daily_file(
    start_date=START_DATE, end_date=END_DATE, wrds_username=WRDS_USERNAME
):
    """
    Pulls monthly CRSP stock data from a specified start date to end date.

    SQL query to pull data, controls for delisting, and importantly
    follows the guidelines that CRSP uses for inclusion, with the exception
    of code 73, which is foreign companies -- without including this, the universe
    of securities is roughly half of what it should be.
    """
    # Not a perfect solution, but since value requires t-1 period market cap,
    # we need to pull one extra month of data. This is hidden from the user.
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    start_date = start_date - relativedelta(months=1)
    start_date = start_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT 
        date,
        dsf.permno, dsf.permco, exchcd, 
        prc, bid, ask, shrout, cfacpr, cfacshr,
        ret, retx
    FROM crsp.dsf AS dsf
    LEFT JOIN 
        crsp.msenames as msenames
    ON 
        dsf.permno = msenames.permno AND
        msenames.namedt <= dsf.date AND
        dsf.date <= msenames.nameendt
    WHERE 
        dsf.date BETWEEN '{start_date}' AND '{end_date}' AND 
        msenames.shrcd IN (10, 11) AND
        msenames.exchcd BETWEEN 1 AND 3
    """
    # with wrds.Connection(wrds_username=wrds_username) as db:
    #     df = db.raw_sql(
    #         query, date_cols=["date", "namedt", "nameendt", "dlstdt"]
    #     )
    db = wrds.Connection(wrds_username=wrds_username)
    df = db.raw_sql(
        query, date_cols=["date"]
    )
    db.close()

    df = df.loc[:, ~df.columns.duplicated()]
    df["shrout"] = df["shrout"] * 1000

    return df

def load_CRSP_daily_file(data_dir=DATA_DIR):
    """
    Load CRSP stock data from disk
    """
    path = Path(data_dir) / "pulled" / "CRSP_stock.parquet"
    return pd.read_parquet(path)

if __name__ == "__main__":

    crsp = pull_CRSP_daily_file(wrds_username=WRDS_USERNAME)
    crsp.to_parquet(DATA_DIR / "pulled" / "CRSP_stock.parquet")