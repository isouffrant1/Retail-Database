from cmath import inf
from flask import Blueprint, render_template, request, session, redirect
from db_connection import cursor, conn
import decimal
from random import randint

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():

    cursor = conn.cursor()
    category = request.form.get('category')

    product_stock = None
    rows = None
    stock_lst = []

    if category == "All":
        cursor.execute("SELECT * FROM Retail_Application.Product")
        rows = cursor.fetchall()

        cursor.execute("SELECT * FROM Retail_Application.Inventory")
        product_stock = cursor.fetchall()

    else:
        cursor.execute( "SELECT * FROM Retail_Application.Product WHERE category = %s", (category, ))
        rows = cursor.fetchall()

        cursor.execute("SELECT ID, Current_Stock FROM Retail_Application.Product INNER JOIN Retail_Application.Inventory ON InventoryID = ID AND category = %s", (category, ))
        product_stock = cursor.fetchall()

    for i in range(len(product_stock)):
        stock_lst.append(product_stock[i][1])

    return render_template("index.html", rows=rows, stock_lst=stock_lst, length=len(rows))


@views.route('/about')
def about():
    return render_template('about.html')

def update_cart(current_cart, item_to_add):
    return dict(list(current_cart.items()) + list(item_to_add.items()))


@views.route('/reviews', methods=["GET", "POST"])
def reviews():
    
    title = request.form.get("title")
    review = request.form.get("review")
    
    print(session['username'])
    if title and review and 'loggedin' in session.keys():
        cursor.execute("Insert into retail_application.reviews(ReviewerID, username, Title, Review) VALUES(%s, %s, %s, %s)", (session['UserID'], session['username'], title, review))
        conn.commit()
    
    cursor.execute("SELECT * FROM Retail_Application.Reviews")
    reviews = cursor.fetchall()
    print(reviews)
    
    return render_template('review.html', reviews= reviews)


@views.route('/cart', methods = ["POST", "GET"])
def cart():
    
    if 'loggedin' in session:
        
        pid = request.form.get('pid')
        qty = request.form.get('qty')     
        
        if pid and qty:
            
            
            cursor.execute("SELECT * FROM Retail_Application.Product WHERE ProductID = %s", (pid, ))
            product = cursor.fetchone()
                        
            temp = qty
            total_price = decimal.Decimal(temp) * product[2]
                        
            cart = {pid: {'name': product[1], 'price': product[2], 'category': product[4], 'image': 'static/' + product[3], 'qty': qty, 'subtotal': total_price, 'CartID': -1}}
            
            if 'most_frequent_NotPresent' not in session:
                session['most_frequent_NotPresent'] = True
            
            cursor.execute("SELECT Tokens from Retail_Application.Users WHERE UserID = %s", (session['UserID'], ))
            tokens = cursor.fetchone()
            session['tokens'] = tokens

            
            
            if 'shopping_cart' in session:
                
                if pid not in session['shopping_cart']:
                    session['shopping_cart'] = update_cart(session['shopping_cart'], cart)
            else:
                session['shopping_cart'] = cart

            cursor.execute('INSERT INTO Retail_Application.ShoppingCart(Quantity, Amount_Due) VALUES (%s, %s)', (qty, session['shopping_cart'][pid]['subtotal']))
            conn.commit()
            
            cursor.execute("SELECT CartID FROM Retail_Application.ShoppingCart WHERE CartID = last_insert_id()")
            cart_id = list(cursor.fetchone())
            
            session['shopping_cart'][pid]['CartID'] = cart_id[0]
            
            cursor.execute('INSERT IGNORE Retail_Application.cart_consistsof_product(CID, PID) VALUES (%s, %s)', (cart_id[0], pid))
            conn.commit()
            
            total = decimal.Decimal('0')
            for value in session['shopping_cart'].values():
                
                total = (decimal.Decimal(value['subtotal']) + decimal.Decimal(total))
            
            session['cart_total'] = total
            
            get_Discount()
                        
            
    return render_template('cart.html')

@views.route('/remove', methods=["GET", "POST"])
def delete_item():
    
    item_id = request.form.get('remove_itemID')
    cart_id = request.form.get('cart_id')
    
    temp = session['shopping_cart']
    
    cursor.execute("SELECT Category FROM retail_application.Product INNER JOIN retail_application.user_shops_product ON user_shops_product.ProductID = Product.ProductID WHERE user_shops_product.UserID = %s GROUP BY category having Count(category) = ( SELECT MAX(most_frequent) as Most_Bought FROM ( SELECT COUNT(category) as most_frequent, Product.category as category FROM retail_application.user_shops_product INNER JOIN retail_application.Product ON product.ProductID = user_shops_product.ProductID WHERE user_shops_product.UserID = %s GROUP BY category)sub);", (1, 1))
    most_bought = cursor.fetchall()
    
    if len(most_bought) == 1:
        for prod in most_bought:
            if prod[0] == temp[item_id]['category']:
                session['most_frequent_NotPresent'] = True
    
    
    temp.pop(item_id,None)    
    session['shopping_cart'] = temp
    
    total = decimal.Decimal('0')
    
    for value in session['shopping_cart'].values():
            total = (decimal.Decimal(value['subtotal']) + decimal.Decimal(total))
    
    session['cart_total'] = total
    
    get_Discount()
    
    return redirect(request.referrer)

@views.route('/tokens', methods=["GET", "POST"])
def apply_token():
    
    tokens = int(request.form.get('token'))
    
    original_tokens = session['tokens']
    updated_token_ct = original_tokens[0] - tokens
    
    cursor.execute("UPDATE retail_application.users SET tokens = %s WHERE UserID = %s", (updated_token_ct, session['UserID']))
    conn.commit()
    
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
    
    position_rewards = [""] * len(temp)
        
    i = 0
    while "" in position_rewards:

        idx = randint(0, len(temp) - 1)

        if position_rewards[idx] == "":
            position_rewards[idx] = temp[i]
            i += 1
                                        
    pick = randint(0, len(position_rewards) - 1)
    reward = position_rewards[pick]
    
    session['reward'] = reward
            
    if 'Discount' in reward:
        
        temp = session['cart_total']
        percentage = 0
        
        if '25% Discount' in reward:
            percentage = 0.25
        elif '10% Discount' in reward:
             percentage = 0.10
        elif '15% Discount' in reward:
            percentage = 0.15
        elif '5% Discount' in reward:
            percentage = 0.05
        elif '50% Discount' in reward:
            percentage = 0.50
        
        temp = decimal.Decimal(temp)
        percentage = decimal.Decimal(percentage)
        
        temp = round(temp - (temp * percentage), 2)
        session['tokens'] = updated_token_ct
        
        for value in session['shopping_cart'].values():
            
            print(decimal.Decimal(value['price']) * decimal.Decimal(percentage))
            amount_paid = round(decimal.Decimal(value['price']) - (decimal.Decimal(value['price']) * percentage), 2)
            value['price'] = amount_paid

            cursor.execute("UPDATE retail_application.ShoppingCart SET Amount_Due = %s WHERE CartID = %s", (value['price'], value['CartID']))
            conn.commit()
                    
        if temp > 0:
            session['cart_total'] = temp
        else:
            session['cart-total'] = decimal.Decimal(0.00)
    
    elif 'tokens' in reward:
        
        multiplier = 0
        
        if 'Double' in reward:
            multiplier = 2
        elif 'Triple' in reward:
            multiplier = 3
        
        new_token_count = (original_tokens[0] * multiplier)
        session['tokens'] = new_token_count
        print(session['tokens'])
        
        cursor.execute("UPDATE retail_application.users SET tokens = %s WHERE UserID = %s", (new_token_count, session['UserID']))        
        conn.commit()

    elif 'Returned' in reward:
        
        added_tokens = 0
        
        if '3' in reward:
            added_tokens = 3
        elif '5' in reward:
            added_tokens = 5
        
        new_token_count = (original_tokens[0] + added_tokens)
        session['tokens'] = new_token_count
        cursor.execute("UPDATE retail_application.users SET tokens = %s WHERE UserID = %s", (new_token_count, session['UserID']))
        conn.commit()
    elif "Dollar" in reward:
        temp = session['cart_total'] 
        temp = decimal.Decimal(temp) - decimal.Decimal(tokens)
        
        if temp > 0:
            session['cart_total'] = temp
        else:
            session['cart_total'] = decimal.Decimal(0.00)
    else:
        session['cart_total'] = decimal.Decimal(0.00)
    
    
    return redirect(request.referrer)
    

def get_Discount():
        
    cursor.execute("SELECT COUNT(*) FROM retail_application.transaction Where UserID = %s", (session['UserID'], ))
    num_of_transactions = cursor.fetchone()
    
    
    if num_of_transactions[0] >= 10:
        cursor.execute("SELECT SUM(Amount_Paid) FROM retail_application.transaction Where UserID = %s", (session['UserID'], ))
        overall_spending = cursor.fetchone()
        
        
        if overall_spending[0] > 1000:
            cursor.execute("SELECT Category FROM retail_application.Product INNER JOIN retail_application.user_shops_product ON user_shops_product.ProductID = Product.ProductID WHERE user_shops_product.UserID = %s GROUP BY category having Count(category) = ( SELECT MAX(most_frequent) as Most_Bought FROM ( SELECT COUNT(category) as most_frequent, Product.category as category FROM retail_application.user_shops_product INNER JOIN retail_application.Product ON product.ProductID = user_shops_product.ProductID WHERE user_shops_product.UserID = %s GROUP BY category)sub);", (1, 1))
            category = cursor.fetchall()
            
                   
            for value in session['shopping_cart'].values():
                for ctg in category:                    
                        if value['category'] == ctg[0]:
                            
                            temp = session['cart_total']
                            cursor.execute("SELECT AVG(Price) FROM Retail_Application.Product INNER JOIN Retail_Application.user_shops_product ON Product.ProductID = user_shops_product.ProductID WHERE UserID = %s", (session['UserID'], ))
                            average = cursor.fetchone()
                            temp = round(abs(decimal.Decimal(average[0]) - decimal.Decimal(temp)), 2)
                        
                            if temp < session['cart_total']:
                                session['cart_total'] = temp
                            
                            break

@views.route('/checkout', methods=["GET", "POST"])
def checkout():

    return render_template('checkout.html')


@views.route('/payment', methods=["GET", "POST"])
def payment():

    if 'loggedin' in session.keys():
        name = request.form.get('Name')
        card_name = request.form.get('card_name')

        address = request.form.get('address')
        city = request.form.get('City')
        state = request.form.get('State')

        zip_code = request.form.get('Zip')
        email = request.form.get('email')
        cvv = request.form.get('cvv')

        credit_c = request.form.get('cc')
        exp_month = request.form.get('mon')
        exp_year = request.form.get('year')

        cursor.execute('INSERT INTO Retail_Application.Transaction(Full_Name, Email, Amount_Paid, Card_num, Name_on_card, ExpiryMonth, CVV, ExpiryYear, Address, City, State, ZipCode, UserID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (name, email, session['cart_total'], credit_c, card_name, exp_month, cvv, exp_year, address, city, state, zip_code, session['UserID']))
        conn.commit()

        cursor.execute('UPDATE Retail_Application.ShoppingCart SET TransactionID = last_insert_id()')
        conn.commit()

        for item in session['shopping_cart']:
            cursor.execute('INSERT IGNORE Retail_Application.User_shops_Product(ProductID, UserID) VALUES (%s, %s)', (item, session['UserID']))
            conn.commit()
        
        session.pop('cart_total', None)
        session.pop('shopping_cart', None)
            
        return "Transaction Succesful!"
    else:
        render_template('login.html')
        
