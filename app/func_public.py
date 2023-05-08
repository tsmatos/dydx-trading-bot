from func_utils import get_ISO_times
from pprint import pprint
import pandas as pd
import numpy as np
from constants import RESOLUTION
import time

# GET RELEVANT TIME PERIODS FOR ISO FROM AND TO
ISO_TIMES = get_ISO_times()

# GET CANDLES RECENT
def get_candles_recent(client, market):
    
    # DEFINE OUTPUT
    close_prices = []
    
    # PROTECT API
    time.sleep(0.2)
    
    # GET DATA
    candles = client.public.get_candles(
        market = market,
        resolution = RESOLUTION,
        limit = 100,
    )
    
    # STRUCTURE DATA
    for candle in candles.data["candles"]:
        close_prices.append(candle["close"])
        
    # CONSTRUCT AND RETURN CLOSE PRICE SERIES
    close_prices.reverse()
    prices_result = np.array(close_prices).astype(float)
    return prices_result

# GET CANDLES HISTORICAL
def get_candles_historical(client, market):
    
    # DEFINE OUTPUT
    close_prices = []
    
    # EXTRACT HISTORICAL PRICE DATA FOR EACH TIMEFRAME
    for timeframe in ISO_TIMES.keys():
        
        # Confirm times needed
        tf_obj = ISO_TIMES[timeframe]
        from_iso = tf_obj["from_iso"]
        to_iso = tf_obj["to_iso"]
        
        # Protect API
        time.sleep(0.2)
        
        # Get Data
        candles = client.public.get_candles(
            market = market,
            resolution = RESOLUTION,
            from_iso = from_iso,
            to_iso = to_iso,
            limit = 100
        )
        
        # Structure Data
        for candle in candles.data["candles"]:
            close_prices.append({"datetime": candle["startedAt"], market: candle["close"]})
            
    # Construct and return DataFrame
    close_prices.reverse()
    return close_prices

# CONSTRUCT MARKET PRICES
def construct_market_prices(client):
    
    # DECLARE VARIABLES
    tradeable_markets = []
    markets = client.public.get_markets()
    
    # FIND TRADEABLE PAIRS
    for market in markets.data["markets"].keys():
        market_info = markets.data["markets"][market]
        
        if market_info["status"] == "ONLINE" and market_info["type"] == "PERPETUAL":
            tradeable_markets.append(market)
            
    # SET INICIAL DATAFRAME
    close_prices = get_candles_historical(client,tradeable_markets[0])
    df = pd.DataFrame(close_prices)
    df.set_index("datetime", inplace=True)
    
    # APPEND OTHER PRICES TO DATAFRAME
    # You can limit the amount to loop though here to save time in development
    for market in tradeable_markets[1:]:
        close_prices_add = get_candles_historical(client, market)
        df_add = pd.DataFrame(close_prices_add)
        df_add.set_index("datetime", inplace=True)
        df = pd.merge(df, df_add, how="outer", on="datetime", copy=False)
        del df_add
        
    # CHECK ANY COLUMNS WITH NANS
    nans = df.columns[df.isna().any()].tolist()
    if len(nans) > 0:
        print("Dropping columns: ")
        print(nans)
        df.drop(columns=nans, inplace=True)
        
    # CREATE AND SAVE DATAFRAME
    df_close_prices = pd.DataFrame(df)
    df_close_prices.to_csv("close_prices.csv")
    
    # RETURN RESULT
    return df
    
