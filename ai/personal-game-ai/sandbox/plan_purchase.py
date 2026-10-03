def purchase(money, price):
    if money >= price:
        return (money - price, True)
    else:
        return (money, False)
