from connections import connect_dydx
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from func_private import abort_all_positions
from func_public import construct_market_prices
from func_cointegration import store_cointegration_results
from func_entry_pairs import open_positions
from func_exit_pairs import manage_trade_exits
from func_messaging import send_message


# MAIN FUNCTION
if __name__ == "__main__":
    
    success = send_message("Wowzers another awesome message!")
    print(success)
    exit(1)
    
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
            
        # STORE COINTEGRATED PAIRS
        try:
            print("Storing cointegrated pairs...")
            stores_result = store_cointegration_results(df_market_prices)
            if stores_result != "saved":
                print("Error saving cointegrated pairs")
                exit(1)
            
        except Exception as e:
            print("Error saving cointegrated pairs: ", e)
            exit(1)
    
    # RUN AS ALWAYS ON
    while True:        
        
        # MANAGE TRADES FOR EXITING POSITIONS
        if MANAGE_EXITS:
            try:
                print("Managing exits...")
                manage_trade_exits(client)
                
            except Exception as e:
                print("Error trading exiting positions: : ", e)
                exit(1)
                
        # PLACE TRADES FOR OPENING POSITIONS
        if PLACE_TRADES:
            try:
                print("Finding opportunities...")
                open_positions(client)
                
            except Exception as e:
                print("Error trading pairs: ", e)
                exit(1)