from connections import connect_dydx
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED
from func_private import abort_all_positions
from func_public import construct_market_prices


if __name__ == "__main__":
    
    # CONNECT TO CLIENT
    try:
        client = connect_dydx()
        print("Connecting to Client...")
        
    except Exception as e:
        print("Error connecting to client: ",e)
        exit(1)
        
    # ABORT ALL POSITIONS
    if ABORT_ALL_POSITIONS:
        try:
            print("Closing all positions...")
            close_order = abort_all_positions(client)
            
        except Exception as e:
            print("Error closing all positions: ", e)
            exit(1)
            
    # FIND COINTEGRATED PAIRS
    if FIND_COINTEGRATED:
        
        # CONSTRUCT MARKET PRICES
        try:
            print("Fetching Market Prices, please allow 3 minutes...")
            df_market_prices = construct_market_prices(client)
            
        except Exception as e:
            print("Error constructing Market Prices: ", e)
            exit(1)