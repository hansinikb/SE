from flask import Flask, render_template, request,session
import mysql.connector
import random
import datetime
import time

app = Flask(__name__)
app.secret_key="hello123"

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Rosie$2729",
    database="cab_booking"
)

mycursor = mydb.cursor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/profile')
def profile():
    customer_id = session['customer_id']
    sql = "SELECT First_name,wallet FROM customer WHERE customer_id = %s"
    mycursor.execute(sql, (customer_id,))
    result = mycursor.fetchone()
    return render_template('dashboard.html',name=result[0], wallet=result[1], customer_id=customer_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        phone = int(request.form['phone'])
        mycursor.execute("SELECT * FROM CUSTOMER")
        myresult = mycursor.fetchall()
        flag = 0
        
        for i in myresult:
            print(name, phone, i[0],i[1],i[2])
            if (i[1] + " " + i[2] == name) and (i[3] == phone):
                customer_id = i[0]
                session['customer_id'] = customer_id
                wallet = i[5]
                return render_template('dashboard.html', name=name, wallet=wallet, customer_id=customer_id)
        if flag == 0:
            return render_template('error.html')
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        FirstName = request.form['FirstName']
        LastName = request.form['LastName']
        Contact = int(request.form['Contact'])
        wallet = float(request.form['wallet'])
        address = request.form['address']
        EmergencyContact = int(request.form['EmergencyContact'])
        Password = request.form['Password']

        random_float1 = random.uniform(1.0, 100.0)
        random_float2 = random.uniform(1.0, 100.0)

        sql = ("INSERT INTO CUSTOMER (CUSTOMER_ID,FIRST_NAME,LAST_NAME,CONTACT_NO,CUST_PASSWORD,WALLET,LOCATION_X,LOCATION_Y,CUST_RATING,ADDRESS,EMERGENCY_CONTACT)" 
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
 
        val = (None, FirstName, LastName, Contact, Password, wallet, random_float1, random_float2, 0, address,
               EmergencyContact)

        mycursor.execute(sql, val)
        mydb.commit()

        mycursor.execute("SELECT * FROM CUSTOMER")

        myresult = mycursor.fetchall()


        for i in myresult:
            if i[1] == FirstName:
                return render_template('dashboard.html', name=FirstName, wallet=wallet, customer_id=i[0])
    return render_template('index.html')

@app.route('/addbalance', methods=['GET', 'POST'])
def add_balance():
    add_amt = request.form["wallet_add"]
    customer_id = session['customer_id']
    sql = "SELECT wallet FROM customer WHERE customer_id = %s"
    mycursor.execute(sql, (customer_id,))
    result = mycursor.fetchone()
    if add_amt!=None:
        current_wallet = result[0]
        new_balance = current_wallet + int(add_amt)
        update_sql = "UPDATE customer SET wallet = %s WHERE customer_id = %s"
        mycursor.execute(update_sql, (new_balance, customer_id))
        mydb.commit()
        #print("Balance added successfully")
    sql = "SELECT First_name,wallet FROM customer WHERE customer_id = %s"
    mycursor.execute(sql, (customer_id,))
    result = mycursor.fetchone()
    return render_template('dashboard.html', name=result[0], wallet=result[1], customer_id=customer_id)

@app.route('/viewrides', methods=['GET','POST'])
def view_rides():
    results = {}
    sql = "SELECT * FROM ride_details WHERE customer_id = %s"
    mycursor.execute(sql,(session['customer_id'],))
    columns = [col[0] for col in mycursor.description]
    rows = mycursor.fetchall()
    print(rows)
    results = {'columns': columns, 'rows': rows}
    return render_template("view.html", results = results)

@app.route('/bookcab', methods=['GET', 'POST'])
def bookcab():
    source = request.form.get("source")
    dest = request.form.get("destination")
    customer_id = session['customer_id']

    sql = "SELECT DRIVER_ID, CONTACT_NO, VEHICLE_NAME, FIRST_NAME, LAST_NAME FROM DRIVER, VEHICLE WHERE DRIVER.VEHICLE_REG_NO = VEHICLE.VEHICLE_REG_NO AND DRIVER.AVAILABILITY = TRUE"
    mycursor.execute(sql)
    available_drivers = mycursor.fetchmany(10)

    est_pay = random.randint(1,500)

    # if est_pay > wallet:
    #     return "You don't have sufficient balance, please add balance"


    driver_selected = request.form.get("driver_name")

    for i in available_drivers:
        if i[3] + " " + i[4] + " - " +i[2] == driver_selected:
            selected_driver_id = i[0]
            driver_name = i[3] + " " + i[4]
            vehicle = i[2]
            
    if(driver_selected):
        sql = ("INSERT INTO RIDE_DETAILS(DRIVER_ID, CUSTOMER_ID, SOURCE_ADDRESS, DESTINATION_ADDRESS, RIDE_DATETIME, COMPLETION_STATUS, PAYMENT_AMOUNT)" 
                "VALUES(%s, %s, %s, %s, %s, %s, %s) ")
        
        now = datetime.datetime.now()

        val = (selected_driver_id, customer_id, source, dest, now, False, None)
        mycursor.execute(sql, val)
        mydb.commit()

        sql = "UPDATE DRIVER SET AVAILABILITY = 1 WHERE DRIVER_ID = %s"
        val = (selected_driver_id,)
        mycursor.execute(sql, val)
        mydb.commit()

        sql = "UPDATE RIDE_DETAILS SET COMPLETION_STATUS = 1 WHERE DRIVER_ID = %s"
        val = (selected_driver_id,)
        mycursor.execute(sql, val)
        mydb.commit()

        sql = "UPDATE RIDE_DETAILS SET PAYMENT_AMOUNT = %s WHERE DRIVER_ID = %s"
        val = (est_pay, selected_driver_id)
        mycursor.execute(sql, val)
        mydb.commit()

        sql = "UPDATE CUSTOMER SET WALLET = WALLET - %s WHERE CUSTOMER_ID = %s"
        val = (est_pay, customer_id)
        mycursor.execute(sql, val)
        mydb.commit()

    sql = "SELECT WALLET FROM CUSTOMER WHERE CUSTOMER_ID = %s"
    mycursor.execute(sql, (customer_id,))
    result = mycursor.fetchone()

    wallet = result[0]

    if(driver_selected):
        return render_template('bookcab.html',
                                    booking_confirmed=True,
                                    driver_name = driver_name,
                                    vehicle = vehicle,
                                    source=source,
                                    dest=dest,
                                    est_pay=est_pay,
                                    wallet=wallet)
    else:
        return render_template('bookcab.html', booking_confirmed = False, available_drivers = available_drivers, wallet = wallet)

if __name__ == '__main__':
    app.run(debug=True)
