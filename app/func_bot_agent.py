from func_private import format_number, check_order_status, place_market_order
from datetime import datetime, timedelta
import time
from pprint import pprint

# CLASS: AGENT FOR MANAGING OPENING AND CHECKING TRADES
class BotAgent:
    
    """
    PRIMARY FUNCTION OF BOTAGENT HANDLES OPENING AND CHECKING ORDER STATUS
    """
    
    # INITIALIZE CLASS
    def __init__(
        self,
        client,
        market_1,
        market_2,
        base_side,
        base_size,
        base_price,
        quote_side,
        quote_size,
        quote_price,
        accept_failsafe_base_price,
        z_score,
        half_life,
        hedge_ratio,
    ):
        
        # INITIALIZE CLASS VARIABLES
        self.client = client 
        self.market_1 = market_1
        self.market_2 = market_2
        self.base_side = base_side
        self.base_size = base_size
        self.base_price = base_price
        self.quote_side = quote_side
        self.quote_size = quote_size
        self.quote_price = quote_price
        self.accept_failsafe_base_price = accept_failsafe_base_price
        self.z_score = z_score
        self.half_life = half_life
        self.hedge_ratio = hedge_ratio
        
        # INITIALIZE OUTPUT VARIABLES
        # Pair status options are FAILED, LIVE, CLOSE, ERROR
        self.order_dict = {
            "market_1": market_1,
            "market_2": market_2,
            "hedge_ratio": hedge_ratio,
            "z_score": z_score,
            "half_life": half_life,
            "order_m1_id": "",
            "order_m1_size": base_size,
            "order_m1_side": base_side,
            "order_m1_time": "",
            "order_m2_id": "",
            "order_m2_size": quote_size,
            "order_m2_side": quote_side,
            "order_m2_time": "",
            "pair_status": "",
            "comments": "",
        }
        
    # CHECK ORDER STATUS BY ID
    def check_order_status_by_id(self, order_id):
        
        # Allow time to process
        time.sleep(2)
        
        # Check order status
        order_status = check_order_status(self.client, order_id)
        
        # Guard: If order cancelled move onto next pair
        if order_status == "CANCELED":
            print(f"{self.market_1} vs {self.market_2} - Order cancelled...")
            self.order_dict["pair_status"] = "FAILED"
            return "failed"
        
        # Guard: If order not filled wait until order expiration
        if order_status != "FAILED":
            time.sleep(15)
            order_status = check_order_status(self.client, order_id)
            
            # Guard: If order cancelled move onto next pair
            if order_status == "CANCELED":
                print(f"{self.market_1} vs {self.market_2} - Order cancelled...")
                self.order_dict["pair_status"] = "FAILED"
                return "failed"
            
            # Guard: If not filled, cancel order
            if order_status != "FILLED":
                self.client.private.cancel_order(order_id = order_id)
                self.order_dict["pair_status"] = "ERROR"
                print(f"{self.market_1} vs {self.market_2} - Order error...")
                return "error"
            
        # RETURN LIVE
        return "live"
        
        
    # OPEN TRADES
    def open_trades(self):
        
        # PRINT STATUS - OPENING FIRST ORDER
        print("---")
        print(f"{self.market_1}: Placing first order...")
        print(f"Side: {self.base_side}, Size: {self.base_size}, Price: {self.base_price}")
        print("---")
        
        # PLACE BASE ORDER
        try: 
            base_order = place_market_order(
                self.client,
                market = self.market_1,
                side = self.base_side,
                size = self.base_size,
                price = self.base_price,
                reduce_only= False
            )
            
            # STORE THE ORDER ID
            self.order_dict["order_m1_id"] = base_order["order"]["id"]
            self.order_dict["order_m1_time"] = datetime.now().isoformat()
            
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 1 - {self.market_1}:  {e}" 
            return self.order_dict
        
        # ENSURE ORDER IS LIVE BEFORE PROCESSING
        order_m1_status = self.check_order_status_by_id(self.order_dict["order_m1_id"])
        
        # GUARD: ABORT IF ORDER FAILED
        if order_m1_status != "live":
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"{self.market_1} failed to fill..."
            return self.order_dict
        
        # PRINT STATUS - OPENING SECOND ORDER
        print("---")
        print(f"{self.market_2}: Placing second order...")
        print(f"Side: {self.quote_side}, Size: {self.quote_size}, Price: {self.quote_price}")
        print("---")
        
        # PLACE QUOTE ORDER
        try: 
            quote_order = place_market_order(
                self.client,
                market = self.market_2,
                side = self.quote_side,
                size = self.quote_size,
                price = self.quote_price,
                reduce_only= False
            )
            
            # STORE THE ORDER ID
            self.order_dict["order_m2_id"] = quote_order["order"]["id"]
            self.order_dict["order_m2_time"] = datetime.now().isoformat()
                        
        except Exception as e:
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"Market 2 - {self.market_2}:  {e}" 
            return self.order_dict
        
        # ENSURE ORDER IS LIVE BEFORE PROCESSING
        order_m2_status = self.check_order_status_by_id(self.order_dict["order_m2_id"])
        
        # GUARD: ABORT IF ORDER FAILED
        if order_m2_status != "live":
            self.order_dict["pair_status"] = "ERROR"
            self.order_dict["comments"] = f"{self.market_2} failed to fill..."
        
            # CLOSE ORDER 1
            try: 
                close_order = place_market_order(
                    self.client,
                    market = self.market_1,
                    side = self.quote_side,
                    size = self.base_size,
                    price = self.accept_failsafe_base_price,
                    reduce_only= True
                )
                
                # ENSURE ORDER IS LIVE BEFORE PROCEEDING
                time.sleep(2)
                order_status_close_order = check_order_status(self.client, close_order["order"]["id"])
                if order_status_close_order != "FILLED":
                    print("ABORT PROGRAM")
                    print("Unexpected Error")
                    print(order_status_close_order)
                    
                    # ! ! ! CONSIDER SENDING MESSAGE HERE ! ! !
                    
                    # ABORT
                    exit(1)
                
            except Exception as e:
                self.order_dict["pair_status"] = "ERROR"
                self.order_dict["comments"] = f"Close Market 1 - {self.market_1}:  {e}"
                print("ABORT PROGRAM")
                print("Unexpected Error")
                print(order_status_close_order)
                    
                # ! ! ! CONSIDER SENDING MESSAGE HERE ! ! !
                    
                # ABORT
                exit(1) 
                
        # RETURN SUCCESS RESULT
        else:
            self.order_dict["pair_status"] = "LIVE"
            return self.order_dict
        
        
        