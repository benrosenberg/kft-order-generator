```
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
```
