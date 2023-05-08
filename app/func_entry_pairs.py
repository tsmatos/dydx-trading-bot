from constants import ZSCORE_THRESHOLD, USD_PER_TRADE, USD_MIN_COLLATERAL
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from func_private import is_open_positions
from func_bot_agent import BotAgent
import pandas as pd
import json
from pprint import pprint

# OPEN POSITIONS
def open_positions(client):
    
    """
    - MANAGE FINDING TRIGGERS FOR TRADE ENTRY
    - STORE TRADES FOR MANAGING LATER ON ON EXIT
    """
    
    # LOAD COINTEGRATED PAIRS
    df = pd.read_csv("cointegrated_pairs.csv")
    
    # GET MARKETS FROM REFERENCING OF MIN ORDER SIZE, TICK SIZE, ETC
    markets = client.public.get_markets().data
    
    # INITIALIZE CONTAINER FOR BOTAGENT
    bot_agents = []
    
    # OPENING JSON FILE
    try:
        open_positions_file = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_file)
        
        for p in open_positions_dict:
            bot_agents.append(p)
                    
    except:
        bot_agents = []
    
    # FIND ZSCORE TRIGGERS
    for index, row in df.iterrows():
        
        # EXTRACT VARIABLES
        base_market = row["base_market"]
        quote_market = row["quote_market"]
        hedge_ratio = row["hedge_ratio"]
        half_life = row["half_life"]
        
        # GET PRICES
        series_1 = get_candles_recent(client, base_market)
        series_2 = get_candles_recent(client, quote_market)
        
        # GET ZSCORE
        if len(series_1) > 0 and len(series_2) == len(series_1):
            spread = series_1 - (hedge_ratio * series_2)
            z_score = calculate_zscore(spread).values.tolist()[-1]
            
        # ESTABLISH IF POTENTIAL TRADE
        if abs(z_score) >= ZSCORE_THRESHOLD:
            
            # Ensure like-for-like not already open (diversify trading)
            is_base_open = is_open_positions(client, base_market)
            is_quote_open = is_open_positions(client, quote_market)
            
            # PLACE TRADE
            if not is_base_open and not is_quote_open:
                
                # Determine side
                base_side = "BUY" if z_score < 0 else "SELL"
                quote_side = "BUY" if z_score > 0 else "SELL"
                
                # Get acceptable price in string format with correct number of decimals
                base_price = series_1[-1]
                quote_price = series_2[-1]
                accept_base_price = float(base_price) * 1.01 if z_score < 0 else float(base_price) * 0.99
                accept_quote_price = float(quote_price) * 1.01 if z_score > 0 else float(quote_price) * 0.99
                failsafe_base_price = float(base_price) * 0.05 if z_score < 0 else float(base_price) * 1.70
                base_tick_size = markets["markets"][base_market]["tickSize"]
                quote_tick_size = markets["markets"][quote_market]["tickSize"]
                
                # Format Prices
                accept_base_price = format_number(accept_base_price, base_tick_size)
                accept_quote_price = format_number(accept_quote_price, quote_tick_size)
                accept_failsafe_base_price = format_number(failsafe_base_price, base_tick_size)
                
                ###### ????? USAR HEDGE RATIO ????? ##############
                # Get size
                base_quantity = 1 / base_price * USD_PER_TRADE
                quote_quantity = 1 / quote_price * USD_PER_TRADE   
                base_step_size = markets["markets"][base_market]["stepSize"]
                quote_step_size = markets["markets"][quote_market]["stepSize"]
                
                # Format sizes
                base_size = format_number(base_quantity, base_step_size)
                quote_size = format_number(quote_quantity, quote_step_size)
                
                # Ensure size
                base_min_order_size = markets["markets"][base_market]["minOrderSize"]             
                quote_min_order_size = markets["markets"][quote_market]["minOrderSize"]            
                check_base = float(base_quantity) > float(base_min_order_size)
                check_quote = float(quote_quantity) > float(quote_min_order_size)
                
                # If checks pass, place trades
                if check_base and check_quote:
                    
                    # Check account balance
                    account = client.private.get_account()
                    free_collateral = float(account.data["account"]["freeCollateral"])
                    print(f"Balance: {free_collateral} and minimun at {USD_MIN_COLLATERAL}")
                    
                    # Guard: Ensure collateral
                    if free_collateral < USD_MIN_COLLATERAL:
                        break
                    
                    # Create a Bot Agent
                    bot_agent = BotAgent(
                        client,
                        market_1  = base_market,
                        market_2  = quote_market,
                        base_side  = base_side,
                        base_size  = base_size,
                        base_price  = accept_base_price,
                        quote_size  = quote_size,
                        quote_side  = quote_side,
                        quote_price  = accept_quote_price,
                        accept_failsafe_base_price = accept_failsafe_base_price,
                        z_score  = z_score,
                        half_life  = half_life,
                        hedge_ratio = hedge_ratio
                    )
                    
                    # Open Trades
                    bot_open_dict = bot_agent.open_trades()
                    
                    # Handle success in opening trades
                    if bot_open_dict["pair_status"] == "LIVE":
                        
                        # Append to list of bot agents
                        bot_agents.append(bot_open_dict)
                        del(bot_open_dict)
                        
                        # Confirm live status in print
                        print("Trade status: Live")
                        print("---")
    
    # SAVE AGENTS
    print(f"Success: Manage open trades checked")
    if len(bot_agents) > 0:
        with open("bot_agents.json", "w") as f:
            json.dump(bot_agents, f)
                    
            
    
    
    
        







