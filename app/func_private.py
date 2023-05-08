from datetime import datetime, timedelta
import time
from pprint import pprint
from func_utils import format_number

# GET EXISTING OPEN POSITIONS
def is_open_positions(client, market):
    
    # PROTECT API
    time.sleep(0.2)
    
    # GET POSITIONS
    all_positions = client.private.get_positions(
        market = market,
        status = "OPEN"
    )
    
    # DETERMINE IF OPEN
    if len(all_positions.data["positions"]) > 0:
        return True
    else:
        return False

# CHECK ORDER STATUS
def check_order_status(client, order_id):
    order = client.private.get_order_by_id(order_id)
    if order.data:
        if "order" in order.data.keys():
            return order.data["order"]["status"]
    return "FAILED"

# PLACE MARKET ORDER
def place_market_order(client, market, side, size, price, reduce_only):
    
    # GET POSITION ID
    account_response = client.private.get_account()
    position_id = account_response.data["account"]["positionId"]
    
    # GET EXPIRATION TIME
    server_time = client.public.get_time()
    expiration = datetime.fromisoformat(server_time.data["iso"].replace("Z","")) + timedelta(seconds=70)
    
    # PLACE AN ORDER
    placed_order = client.private.create_order(
        position_id = position_id,
        market = market,
        side = side,
        order_type = "MARKET",
        post_only = False,
        size = size,
        price = price,
        limit_fee = '0.015',
        expiration_epoch_seconds = expiration.timestamp(),
        time_in_force = "FOK",
        reduce_only = reduce_only
    )
    
    # RETURN RESULT
    return placed_order.data
    

# ABORT ALL OPEN POSITIONS
def abort_all_positions(client):
    
    # CANCEL ALL ORDERS
    client.private.cancel_all_orders()
    
    # PROTECT API
    time.sleep(0.5)
    
    # GET MARKETS FOR REFERENCE OF TICK SIZE (TOTAL = 38 MARKETS)
    markets = client.public.get_markets().data
        
    # GET ALL OPEN POSITIONS
    positions = client.private.get_positions(status="OPEN")
    all_positions = positions.data["positions"]
    
    # HANDLE OPEN POSITIONS
    close_orders = []
    if len(all_positions) > 0:
        
        # Loop through each position
        for position in all_positions:
            
            # Determine the Market
            market = position["market"]
            
            # Determine the Side
            side = "BUY"
            if position["side"] == "LONG":
                side = "SELL"
                
            # Get Price
            price = float(position["entryPrice"])
            accept_price = price * 1.7 if side == "BUY" else price * 0.3
            tick_size = markets["markets"][market]["tickSize"]
            accept_price = format_number(accept_price, tick_size)
            
            # Place Order to Close
            order = place_market_order(
                client = client,
                market = market,
                side = side,
                size = position["sumOpen"],
                price = accept_price,
                reduce_only = True
            )
            
            # Append the Result
            close_orders.append(order)
            
            # Protect API
            time.sleep(0.2)
            
        # Return Closed Orders
        return close_orders
            
            