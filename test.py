from random import randint


# test = [(1, 1, 'jakedoe1', 'Outstanding Review Design', 'I had great experience shopping on this website; very user-friendly and worth it.'), (2, 1, 'jakedoe1', 'Outstanding Review Design', 'I had great experience shopping on this website; very user-friendly and worth it.'), (3, 1, 'jakedoe1',
#                                                                                                                                                                                                                                                                                      'Outstanding Review Design', 'I had great experience shopping on this website.'), (4, 1, 'jakedoe1', 'Outstanding Review Design', 'I had great experience shopping.'), (5, 1, 'jakedoe1', 'Outstanding Review Design', 'I had great experience.'), (6, 1, 'jakedoe1', 'Outstanding Review Design', 'I had good experience.')]

# for item in test:
#     print(item[2])
#     print(item[3])
#     print(item[4])
#     print()


tokens = 3

rewards = [ 
            "5% Discount on active purchase", "10% Discount on active purchase", "15% Discount on active purchase", "Returned investment plus 3",
            "25% Discount on active purchase", "50% Discount on active purchase", "30% Discount on acitve purchase", "Returned investment plus 5", 
            "Dollar Off per token", "Free purchase", "Double the tokens", "Triple the tokens"
            ]
    
    
temp = rewards
      
if tokens < 8:
        temp.remove("Free purchase")
        temp.remove("Double the tokens")
        temp.remove("Triple the tokens")
        temp.remove("Dollar Off per token")
    
        if tokens < 4:
            temp.remove("30% Discount on acitve purchase")
            temp.remove("50% Discount on active purchase")
               
        
position_rewards = [""] * len(rewards)
        
i = 0
while "" in position_rewards:

    idx = randint(0, len(temp) - 1)

    if position_rewards[idx] == "":
        # replace
        position_rewards[idx] = temp[i]
        i += 1
    
                
    # position_rewards = temp

print(position_rewards)




# -- SELECT Category
# -- FROM Product INNER JOIN user_shops_product ON user_shops_product.ProductID = Product.ProductID
# -- WHERE user_shops_product.UserID = 2
# -- GROUP BY category
# -- HAVING COUNT(category) = (
# --     SELECT MAX(most_frequent) as Most_Bought
# --     FROM (
# --         SELECT COUNT(category) as most_frequent, Product.category as category
# --         FROM user_shops_product
# --         INNER JOIN Product ON product.ProductID = user_shops_product.ProductID
# --         WHERE user_shops_product.UserID = 2
# --         GROUP BY category
# --     ) sub
# -- );

# -- SELECT AVG(Price) as average
# -- FROM Product INNER JOIN user_shops_product ON Product.ProductID = user_shops_product.ProductID
# -- WHERE UserID = 2;
