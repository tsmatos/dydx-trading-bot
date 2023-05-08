from constants import CLOSE_AT_ZSCORE_CROSS
from func_utils import format_number
from func_public import get_candles_recent
from func_cointegration import calculate_zscore
from  func_private import place_market_order
import json
import time
from pprint import pprint

# CLOSE POSITIONS
def manage_trade_exits(client):
    
    """
    Manage exiting open poitions based upon criteria set in constants
    """
    
    # INITIALIZE SAVING OUTPUTS
    save_output = []
    
    # OPENING JSON FILE
    try:
        open_positions_file = open("bot_agents.json")
        open_positions_dict = json.load(open_positions_file)
    except:
        return "complete"
    
    # Guard: Exit if no open positions in file
    if(len(open_positions_dict)) < 1:
        return "complete"
    
    # GET ALL POSITIONS PER TRADING PLATFORM
    exchange_pos = client.private.get_positions(status="OPEN")
    all_exc_pos = exchange_pos.data["positions"]
    markets_live = []
    for p in all_exc_pos:
        markets_live.append(p["market"])
    
    # PROTECT API
    time.sleep(0.5)
        
    # CHECK ALL SAVED POSITIONS MATCH ORDER RECORD
    # Exit trade according to any exit trade rules
    for position in open_positions_dict:
        
        # INITIALIZE IS_CLOSE TRIGGER
        is_close = False
        
        # EXTRACT POSITION MATCHING INFORMATION FROM FILE - MARKET 1
        position_m1_market = position["market_1"]
        position_m1_size = position["order_m1_size"]
        position_m1_side = position["order_m1_side"]
        
        # EXTRACT POSITION MATCHING INFORMATION FROM FILE _ MAKET 2
        position_m2_market = position["market_2"]
        position_m2_size = position["order_m2_size"]
        position_m2_side = position["order_m2_side"]
        
        # PROTECT API
        time.sleep(0.5)
        
        # GET ORDER INFO M1 PER EXCHANGE
        order_m1 = client.private.get_order_by_id(position["order_m1_id"])
        order_m1_market = order_m1.data["order"]["market"]
        order_m1_size = order_m1.data["order"]["size"]
        order_m1_side = order_m1.data["order"]["side"]
        
        # PROTECT API
        time.sleep(0.5)
        
        # GET ORDER INFO M2 PER EXCHANGE
        order_m2 = client.private.get_order_by_id(position["order_m2_id"])
        order_m2_market = order_m2.data["order"]["market"]
        order_m2_size = order_m2.data["order"]["size"]
        order_m2_side = order_m2.data["order"]["side"]
        
        # PERFORM MATCHING CHECKS
        check_m1 = position_m1_market == order_m1_market and position_m1_size == order_m1_size and position_m1_side == order_m1_side
        check_m2 = position_m2_market == order_m2_market and position_m2_size == order_m2_size and position_m2_side == order_m2_side
        check_live = position_m1_market in markets_live and position_m2_market in markets_live
        
        # Guard: If not all match exit woth error
        if not check_m1 or not check_m2 or not check_live:
            print(f"Warning: Not all open positions match exchange records for {position_m1_market} and {position_m2_market}")
            continue
        
        # GET PRICES
        series_1 = get_candles_recent(client, position_m1_market)
        time.sleep(0.2)
        series_2 = get_candles_recent(client, position_m2_market)
        time.sleep(0.2)
        
        # GET MARKETS FOR REFERENCE OF TICK SIZE
        markets = client.public.get_markets().data
        
        # PROTECT API
        time.sleep(0.2)
        
        # TRIGGER CLOSE BASED ON Z-SCORE
        if CLOSE_AT_ZSCORE_CROSS:
            
            # INITIALIZE Z_SCORES
            hedge_ratio = position["hedge_ratio"]
            z_score_traded = position["z_score"]
            
            if len(series_1) > 0 and len(series_1) == len(series_2):
                spread = series_1 - (hedge_ratio * series_2)
                z_score_current = calculate_zscore(spread).values.tolist()[-1]
                
            # DETERMINE TRIGGER
            z_score_level_check = abs(z_score_current) >= abs(z_score_traded)
            z_score_cross_check = (z_score_current < 0 and z_score_traded > 0) or (z_score_current > 0 and z_score_traded < 0)
            
            # CLOSE TRADE
            if z_score_level_check and z_score_cross_check:
                
                # Initiate close trigger
                is_close = True
                
        #####
        # Add any other close logic you want here
        # Trigger is_close
        #####        
        
        # CLOSE POSITIONS IF TRIGGERED
        if is_close:
            
            # DETERMINE SIDE M1
            side_m1 = "SELL"
            if position_m1_side == "SELL":
                side_m1 = "BUY"
            
            # DETERMINE SIDE M2
            side_m2 = "SELL"
            if position_m2_side == "SELL":
                side_m2 = "BUY"
                
            # GET AND FORMAT PRICE
            price_m1 = float(series_1[-1])
            price_m2 = float(series_2[-1])
            accept_price_m1 = price_m1 * 1.05 if side_m1 == "BUY" else price_m1 * 0.95
            accept_price_m2 = price_m2 * 1.05 if side_m2 == "BUY" else price_m2 * 0.95
            tick_size_m1 = markets["markets"][position_m1_market]["tickSize"]
            tick_size_m2 = markets["markets"][position_m2_market]["tickSize"]
            accept_price_m1 = format_number(accept_price_m1, tick_size_m1)
            accept_price_m2 = format_number(accept_price_m2, tick_size_m2)
            
            # CLOSE POSITIONS
            try:
                
                # Close Position for Market 1
                print(">>> Closing market 1 <<<")
                print(f"Closing position for {position_m1_market}")
                
                close_order_m1 = place_market_order(
                    client,
                    market = position_m1_market,
                    side = side_m1,
                    size = position_m1_size,
                    price = accept_price_m1,
                    reduce_only = True
                )
                
                
                print(close_order_m1["order"]["id"])
                print(">>> Closing <<<")
                
                # Protect API
                time.sleep(1)
                
                # Close Position for Market 2
                print(">>> Closing market 2 <<<")
                print(f"Closing position for {position_m2_market}")
                
                close_order_m2 = place_market_order(
                    client,
                    market = position_m2_market,
                    side = side_m2,
                    size = position_m2_size,
                    price = accept_price_m2,
                    reduce_only = True
                )
                
                
                print(close_order_m2["order"]["id"])
                print(">>> Closing <<<")
                
                # Protect API
                time.sleep(1)
                
            except Exception as e:
                print(f"Exit failed for {position_m1_market} with {position_m2_market}")
                save_output.append(position)
                
        # KEEP RECORD IF ITEMS AND SAVE
        else:
            save_output.append(position)
                
    # SAVE REMAINING ITEMS
    print(f"{len(save_output)} Item remaining. Saving file...")
    with open("bot_agents.json", "w") as f:
        json.dump(save_output, f)
            
            
                
            
                
    