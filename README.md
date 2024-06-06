Here's how we derive the result:
- We count every successful order.
- We consider an order as failed if:
1. It doesn't have the error 'bad scoring' (rejected by Sardine).
2. We treat duplicate failed orders with the same errors from a user to the one partner ID on the same day as one failed order.
3. We don't count a failed order if there was at least one successful order on the same day.


Don't forget to install:

pip install pandas
pip install pycountry
