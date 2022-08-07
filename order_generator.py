import json, random, datetime, sys

helpmsg = ('''
    Help for KFT Order Generator
    ----------------------------
    This script generates orders for Kung Fu Tea, with the intent to 
    ensure that the orders are as "novel" as possible. Novelty is 
    defined in the form of penalties, where the penalty given by having 
    a certain item D days in the past for novelty renewal period N is
    as follows:

        max(1 - sqrt(N * D)/N, 0)

    Commands:

    ... help:       Show this help page
    ... clear:      Clear order history
    ... (no args):  Generate a new order and add to history
''')

order_storage = 'previous_orders.json'

novelty_reset = 5

class Order:
    """Class for a KFT order"""

    # tea types (does not include "seasonal" or "what's new" varieties)
    tea_types = ['classic', 'milk tea', 'punch', 'milk cap', 'yogurt', 'slush', 'milk strike', 'espresso']

    # ice categories
    ice_categories = ['no', 'less', 'regular', 'more']

    # toppings (only relevant toppings listed)
    topping_list = ['tapioca', 'pudding', 'nata jelly', 'red bean', 'coffee popping bubbles', 'herbal jelly', 'grape popping bubbles', 'aloe jelly', 'mango popping bubbles', 'lychee crystal bubbles']
    
    # from_uniform = True means that all numbers provided are floats x : 0.0 <= x <= 1.0
    def __init__(self, toppings, tea_type, sugar_percentage, ice_category, from_uniform=False):
        if not from_uniform:
            self.toppings = [self.topping_list[t % len(self.topping_list)] for t in toppings]
            self.tea_type = self.tea_types[tea_type % len(self.tea_types)]
            self.sugar_percentage = sugar_percentage % 100
            self.ice_category = self.ice_categories[ice_category % len(self.ice_categories)]
        else:
            self.toppings = [self.topping_list[int(t * len(self.topping_list))] for t in toppings]
            self.tea_type = self.tea_types[int(tea_type * len(self.tea_types))]
            self.sugar_percentage = int(sugar_percentage * 100)
            self.ice_category = self.ice_categories[int(ice_category * len(self.ice_categories))]

    def __str__(self):
        if len(self.toppings) == 1:
            topping_list_formatted = self.toppings[0]
        elif len(self.toppings) == 2:
            topping_list_formatted = ' and '.join(self.toppings)
        else:
            insert_before_end = lambda l, s : l[:-1] + [s] + l[-1:]
            topping_list_formatted = ', '.join(insert_before_end(self.toppings, 'and')).replace(' and,', ' and') 
        return f"A {self.tea_type} tea with {topping_list_formatted} with {self.sugar_percentage} percent sugar and {self.ice_category} ice."

    def to_dict(self):
        return {
            'toppings' : [self.topping_list.index(t) for t in self.toppings],
            'tea_type' : self.tea_types.index(self.tea_type),
            'sugar_percentage' : self.sugar_percentage,
            'ice_category' : self.ice_categories.index(self.ice_category)
        }

    @staticmethod
    def generate_first():
        """
        Generate first order, as a list of __init__ function arguments. Has no memory of previous orders.
           
        The dictionary output "args" should be used with Order.__init__(**args).
        """
        return {
            'toppings' : [t/len(Order.topping_list) for t in random.choices(range(len(Order.topping_list)), k=random.choice(range(1,4)))],
            'tea_type' : random.random(),
            'sugar_percentage' : random.random(),
            'ice_category' : random.random(),
            'from_uniform' : True
        }
            

def novelty_penalty(days):
    """
    Returns a penalty in [0.0, 1.0] depending on the number of days that have passed
    since the last time this item was ordered.
    Precond.: days >= 0
    """
    return max(1 - ((novelty_reset * days)**0.5)/novelty_reset, 0)

def new_order():
    today = datetime.date.today()

    with open(order_storage, 'r') as prev_order_file:
        order_dict = json.load(prev_order_file)
        previous_orders = order_dict['orders']
    
    if len(previous_orders) == 0:
        this_order = Order(**Order.generate_first())
        this_order_dict = this_order.to_dict()
        this_order_dict['date'] = str(today)
        updated_orders = {'orders' : [ this_order_dict ]}
    else:
        # calculate "novelty factor" of each ingredient, relatively
        # note here that we don't care about novelty for sugar_percentage as it is not categorical data
        novelty_factors = {
            'toppings' : [1 for _ in Order.topping_list], 
            'tea_type' : [1 for _ in Order.tea_types], 
            'ice_category' : [1 for _ in Order.ice_categories]
        }
        # iterate through previous orders, applying function given timedeltas
        for order in previous_orders:
            days_since = (today - datetime.datetime.fromisoformat(order['date']).date()).days
            penalty = novelty_penalty(days_since)
            for topping in order['toppings']:
                novelty_factors['toppings'][topping] = max(novelty_factors['toppings'][topping] - penalty, 0)
            novelty_factors['tea_type'][order['tea_type']] = max(novelty_factors['tea_type'][order['tea_type']] - penalty, 0)
            novelty_factors['ice_category'][order['ice_category']] = max(novelty_factors['ice_category'][order['ice_category']] - penalty, 0)
        # apply these weights to create generation distribution, and choose items for order
        args = {
            'toppings' : [],
            'tea_type' : 0,
            'sugar_percentage' : int(random.random() * 100),
            'ice_category' : 0,
            'from_uniform' : False
        }
        for k,v in novelty_factors.items():
            v_or_none = None if sum(v) == 0 else v
            if k == 'toppings': # choose between 1 and 3 toppings (need to remove duplicates)
                args[k] = list(set(random.choices(range(len(v)), weights=v_or_none, k=random.choice(range(1,4)))))
            else:
                args[k] = random.choices(range(len(v)), weights=v_or_none, k=1)[0]
        # generate new order and add to running order list
        this_order = Order(**args)
        this_order_dict = this_order.to_dict()
        this_order_dict['date'] = str(today)
        previous_orders.append(this_order_dict)
        updated_orders = {'orders' : previous_orders}

    print("Today's order:", str(this_order), sep='\n')

    with open(order_storage, 'w') as prev_order_file:
        json.dump(updated_orders, prev_order_file)

def clear_orders():
    response = input('Are you sure you want to clear order history? [y/N] ')
    if set(response) & set('yY'):
        with open(order_storage, 'w') as prev_order_file:
                json.dump({"orders" : []}, prev_order_file)
    else:
        print('Aborted.')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        new_order()
    elif sys.argv[1] == 'clear':
        clear_orders()
    elif sys.argv[1] == 'help':
        print(helpmsg)
