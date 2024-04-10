from flask import Flask, jsonify, request # handling the import, giving us access to Flask and its functionality
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError
# local import for db connection
from connect_db import connect_db, Error

app = Flask(__name__) #instatiates our flask app and points it to the current file

ma = Marshmallow(app)

# define the customer schema
# makes sure the customer data adheres to a specific format
class CustomerSchema(ma.Schema):
    customer_id = fields.Int(dump_only=True)
    name = fields.String(required=True)
    email = fields.String(required=True)
    phone = fields.String(required=True)

    class Meta:  
        
        fields = ("customer_id", "name", "email", "phone")
# instantiating CustomerSchema class
# based on how many customers we're dealing with
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

# MVC model
# Model - What do tables in my database look like -- comes from classes
# View - what is being rendered at each route html, usually in the form of templates
# Controller - routes the traffic through the broswer

# flask marshmallow Notes
# we dont need to check manually that data exists
# flask marshmallow schemas will check for relevant data and that it fits
# the specified structure
# WE DONT NEED TO DO THIS:
# customer_data = request.json
# if not customer_data:
#     return jsonify({"error": "No data provided"}), 400

# Status Codes:
# 200 - OK
# Everything is working, the request was succesful!
# 201 - CREATED
# succesful request and a new resource has been created
# 204 - NO CONTENT
# AFter a delete request - the resource was succesfully deleted
# 300 - General Redirection, moving between routes
# 400 - Bad Request/request failed
# the request was invalid or cannot be served
# 401 - UNAUTHORIZED
# request that user authentication - no permission
# 403 - FORBIDDEN
# The request is valid but the server is refusing it or access is not allowed
# 404 - Not Found
# There is no resource available
# 500 - Internal Server Error
# request cannot be connected to the api
@app.route("/") #traffic controller
def home():
    return "Welcome to our super cool ecommerce api! yippee"

# @app.route("/about")
# def about():
#     return "Hello! My name is Ryan and I like to party."

# get request to grab all customer information
@app.route('/customers', methods=['GET'])
def get_customers(): 
    print("hello from the get")  
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(dictionary=True)
        # SQL query to fetch all customers
        query = "SELECT * FROM Customer"

        # executing query with cursor
        cursor.execute(query)

        # accessing stored query
        customers = cursor.fetchall()

         # use Marshmallow to format the json response
        return customers_schema.jsonify(customers)
    
    except Error as e:
        # error handling for connection/route issues
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close() 


#                          to create or send data to our server
@app.route('/customers', methods = ['POST']) 
def add_customer():
    try:
        # Validate the data follows our structure from the schema
        # deserialize the data using Marshmallow
        # this gives us a python dictionary
        customer_data = customer_schema.load(request.json)

    except ValidationError as e:
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # new customer details, to be sent to our db
        # comes from customer_data which we turn into a python dictionary
        # with .load(request.json)
        new_customer = (customer_data['name'], customer_data['email'], customer_data['phone'])

        # SQL Query to insert customer data into our database
        query = "INSERT INTO Customer (name, email, phone) VALUES (%s, %s, %s)"

        # execute the query 
        cursor.execute(query, new_customer)
        conn.commit()

        # Succesfiul addition of our customer
        return jsonify({"message":"New customer added succesfully"}), 201
    
    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close() 

@app.route('/customers/<int:id>', methods= ["PUT"])
def update_customer(id):
    print("hello")
    try:
        # Validate the data follows our structure from the schema
        # deserialize the data using Marshmallow
        # this gives us a python dictionary
        customer_data = customer_schema.load(request.json)
        print(customer_data)

    except ValidationError as e:
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

        # Updating customer info
        updated_customer = (customer_data['email'], id)

        # SQL Query to find and update a customer based on the id
        query = "UPDATE Customer SET email = %s WHERE customer_id = %s"

        # Executing Query
        cursor.execute(query, updated_customer)
        conn.commit()

        # Message for succesful update
        return jsonify({"message":"Customer details were succesfully updated!"}), 200
    
    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/customers/<int:id>', methods=["DELETE"])
def delete_customer(id):
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        # set variable for the id passed in through the right to a tuple, with that
        customer_to_remove = (id,)
        

        # query to find customer based on their id
        query = "SELECT * FROM Customer WHERE customer_id = %s"
        # check if customer exists in db
        cursor.execute(query, customer_to_remove)
        customer = cursor.fetchone()
        if not customer:
            return jsonify({"error": "User does not exist"}), 404
        
        # If customer exists, we shall delete them :( 
        del_query = "DELETE FROM Customer where customer_id = %s"
        cursor.execute(del_query, customer_to_remove)
        conn.commit()

        # nice message about the execution of our beloved customer
        return jsonify({"message":"Customer Removed succesfully"}), 200   



    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close() 

# ================= ORDER SCHEMA and ROUTES ============================
class OrderSchema(ma.Schema):
    order_id = fields.Int(dump_only=True)
    customer_id = fields.Int(required=True)
    date = fields.Date(required=True)
    class Meta:  
        
        fields = ("order_id", "customer_id", "date")
# initialize our schemas
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)

    

@app.route("/orders", methods = ["GET"])
def get_orders():
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM orders"
        cursor.execute(query)
        orders = cursor.fetchall()  

        return orders_schema.jsonify(orders)
    
    
    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    
    finally:
        #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close() 

# POST request to add ordere
@app.route('/orders', methods=["POST"])
def add_order():
    try:
        # Validate incoming data
        order_data = order_schema.load(request.json)

    except ValidationError as e:
        return jsonify(e.messages), 400

    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        
        query = "INSERT INTO orders (date, customer_id) VALUES (%s,%s)"
        cursor.execute(query, (order_data['date'], order_data['customer_id']))
        conn.commit()
        return jsonify({"message": "Order was succesfully added"}),201


    

    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
    #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close() 

# PUT request to Update Order
@app.route('/orders/<int:order_id>', methods= ["PUT"])
def update_order(order_id):
    try:
        # Validate incoming data
        order_data = order_schema.load(request.json)

    except ValidationError as e:
        return jsonify(e.messages), 400
    
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()
        query = "UPDATE ORDERS SET date = %s, customer_id = %s WHERE order_id = %s"
        cursor.execute(query, (order_data['date'], order_data['customer_id'], order_id))
        conn.commit()
        return jsonify({"message": "Order updated succesfully"}), 200    


    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
    #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    
# DELETE Request
@app.route("/orders/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    try:
        conn = connect_db()
        if conn is None:
            return jsonify({"error": "Database connection failed"}), 500
        cursor = conn.cursor()

         # query to find order based on their id
        query = "SELECT * FROM Orders WHERE order_id = %s"
        # check if order exists in db
        cursor.execute(query, (order_id,))
        order = cursor.fetchone()
        if not order:
            return jsonify({"error": "Order does not exist"}), 404
        
        # If customer exists, we shall delete them :( 
        del_query = "DELETE FROM Orders where order_id = %s"
        cursor.execute(del_query, (order_id,))
        conn.commit()
        return jsonify({"message": f"Succesfully delete order_id {order_id}"})     

    except Error as e:
        print(f"error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
    #checking again for connection object
        if conn and conn.is_connected():
            cursor.close()
            conn.close()







    


       





if __name__ == "__main__":

    app.run(debug=True)

