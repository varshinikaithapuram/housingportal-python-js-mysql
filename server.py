from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
from flask_mysqldb import MySQL
from random import randint
import traceback,os
from collections import defaultdict
from flask import session


from flask import Flask, request, session, redirect, url_for, render_template, flash, jsonify
import os
from models import db,User, chatRoom, messageLog
from flask_mysqldb import MySQL

app = Flask(__name__)

# Database configuration
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'development key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Balok@31@localhost/housing'  # Use your MySQL credentials and database name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Initialize SQLAlchemy with the app
db.init_app(app)

@app.cli.command('initdb')
def initdb_command():
    cur = mysql.connection.cursor()
    with app.open_resource('schema.sql', mode='r') as f:
        cur.execute(f.read())
    cur.close()
    mysql.connection.commit()
    print('Initialized the database.')

app.secret_key = 'my unobvious secret key'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Balok@31'
app.config['MYSQL_DB'] = 'housing'
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app)


@app.route('/')
def main():
    return render_template('main.html')

# @app.route('/index', methods=['GET', 'POST'])
# def index():
#     return render_template('index.html')

@app.route('//indexi')
def get_apartments():

  cur = mysql.connection.cursor()
  cur.execute("SELECT apartment.doorno, apt_detail.description, apartment.img FROM apt_detail INNER JOIN apartment ON apt_detail.apt_detail_code = apartment.apt_detail_code")
  
  apartments = cur.fetchall()
  
  return jsonify(apartments)

@app.route('/search')
def search():
    # Get the search parameters from the query string
    beds = int(request.args.get('beds'))
    baths = int(request.args.get('baths'))
    cost = (request.args.get('cost'))
    cur = mysql.connection.cursor()
  
    # Perform the search query
    cur.execute(
        "SELECT * FROM apartment JOIN apt_detail ON apartment.apt_detail_code = apt_detail.apt_detail_code "
        "WHERE bhk<=%s AND bathroom<=%s AND price<=%s",
        (beds, baths, cost)
    )

    # Fetch all matching apartments
    results = cur.fetchall()
    cur.close()
    # Convert the results to a list of dictionaries for easier processing
    apartment_list = []
    for row in results:

        apartment = {
            "apt_id": row[0],
            "bhk": row[1],
            "bathroom": row[2],
            "size": row[3],
            "description": row[4],
            "price": row[5],
            "img": row[7]        
            }
        apartment_list.append(apartment)

    return jsonify(apartment_list)

@app.route('/index',methods = ['GET','POST'])
def home():
    if request.method == 'POST':
        username = request.form['admin_username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute('''SELECT * FROM admin WHERE (admin_username, password) = (%s,%s)''',(username,password))
        n = cur.fetchall()
        if len(n)!=0:
            print (n)
            return render_template('admin-logged.html')
        else:
            print (n)
            return render_template('index.html')
    return render_template('index.html')

@app.route('/home',methods = ['GET','POST'])
def homepage():
    return render_template('home.html')
@app.route('/apartment', methods=['GET', 'POST'])
def apartment():
    data = []
    cur = mysql.connection.cursor()
    cur.execute('''select apt_id, `doorno`, `price`, `status`, `img`, bhk, bathroom, size, name, phone 
                   from apartment a, apt_detail a1, person p 
                   where a.apt_detail_code=a1.apt_detail_code and p.per_id = a.owner_per_id''')
    rows = cur.fetchall()
    print(rows)
    if not rows:
        return render_template('apartmentnull.html')
    else:
        for row in rows:
            row = list(row)
            if row[3] == "n":
                row[3] = "none"
                row.append("bg-light text-secondary")
            else:
                row[3] = "auto"
                row.append("btn-primary")
            data.append(row)
        return render_template('apartment.html', data=data)
    
@app.route('/communities', methods=['GET', 'POST'])
def communities():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM society''')
    data = cur.fetchall()
    print(data)

    return render_template('communities.html', data=data)


@app.route('/specificapt/<build>', methods=['GET', 'POST'])
def specificapt(build):
    data = []
    sid = build
    cur = mysql.connection.cursor()

    # Fetch apartment details and facility data
    cur.execute('''SELECT apt_id, doorno, price, status, a.img, bhk, bathroom, size, p.name, phone, s.name 
        FROM apartment a, apt_detail a1, person p, society s 
        WHERE a.apt_detail_code=a1.apt_detail_code AND p.per_id = a.owner_per_id AND s.sid=a.sid AND a.sid = %s''', (sid,))
    rows = cur.fetchall()

    cur.execute('''SELECT facility, image FROM facility WHERE sid=%s''', (sid,))
    fac_data = cur.fetchall()

    # Process apartment data
    for row in rows:
        row = list(row)
        if row[3] == "n":
            row[3] = "none"
            row.append("bg-light text-secondary")
        else:
            row[3] = "auto"
            row.append("btn-primary")
        data.append(row)
   
    # Check if there are no apartments found
    blank_apartment = [[' ']]
    no_apartments = len(data) == 0
    if no_apartments:
       cur = mysql.connection.cursor()
       cur.execute('''SELECT name FROM society WHERE sid=%s''', (sid))
       blank_apartment = cur.fetchall()
       print(blank_apartment)
    return render_template('specific-apt.html', data=data, fac_data=fac_data, no_apartments=no_apartments,blank_apartment=blank_apartment )


@app.route('/addapt', methods=['GET', 'POST'])
def addapt():
    try:
        if request.method == 'POST':
            apt_id = request.form['apt_id']
            sid = request.form['sid']
            apt_detail_code = request.form['apt_detail_code']
            door_no = request.form['door_no']
            owner = request.form['owner_id']
            price = request.form['price']
            image = request.files['image']

            if image:
                image.save(os.path.join('static/apartments', image.filename))

            if (owner == '' or owner == 'null'):
                cur = mysql.connection.cursor()
                cur.execute('''INSERT INTO apartment(apt_id, sid, apt_detail_code, doorno, price, img) 
                            VALUES(%s,%s,%s,%s,%s,%s)''', (apt_id, sid, apt_detail_code, door_no, price, image.filename))
                mysql.connection.commit()
            else:
                cur = mysql.connection.cursor()
                cur.execute('''INSERT INTO apartment(apt_id, sid, apt_detail_code, doorno, owner_per_id, price, img, status) 
                            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)''',
                            (apt_id, sid, apt_detail_code, door_no, owner, price, image.filename, 'n'))
                mysql.connection.commit()
    except:
        print('bad')
        print(traceback.print_exc())

    cur = mysql.connection.cursor()
    cur.execute('''SELECT apt.apt_id, soc.name, ad.description, apt.doorno, per.name, apt.price, apt.status, apt.img 
                   FROM apartment apt
                   LEFT JOIN society soc ON apt.sid = soc.sid
                   LEFT JOIN apt_detail ad ON apt.apt_detail_code = ad.apt_detail_code
                   LEFT JOIN person per ON apt.owner_per_id = per.per_id''')
    data = cur.fetchall()

    # Fetch data for the "society" table to populate the dropdown list
    cur.execute('''SELECT sid, name FROM society''')
    society_data = cur.fetchall()
    # Fetch data for the "person" table to populate the dropdown list
    cur.execute('''SELECT per_id, name FROM person''')
    owner_data = cur.fetchall()
    # Fetch data for the "apt_detail" table to populate the dropdown list
    cur.execute('''SELECT apt_detail_code, description FROM apt_detail''')
    aptdetail_data = cur.fetchall()

    return render_template('admin-apartment-insert.html', data=data, society_data=society_data, owner_data=owner_data, aptdetail_data=aptdetail_data)


@app.route('/addadmin', methods = ['GET','POST'])
def addadmin():
     try:
         if request.method == 'POST':
             username = request.form['admin_username']
             password = request.form['password']
             cur = mysql.connection.cursor()
             cur.execute('''INSERT INTO admin(admin_username,password) VALUES (%s,%s)''',(username,password))
             mysql.connection.commit()
     except:
         print ('bad')
     cur = mysql.connection.cursor()
     cur.execute('''SELECT * FROM admin''')
     data = cur.fetchall()
     return render_template('admin-add.html', data = data)

@app.route('/deladmin', methods = ['GET','POST'])
def deladmin():
    try:
        if request.method == 'POST':
            admin_id = request.form['admin_id']
            password = request.form['password']
            #print admin_id,password
            cur = mysql.connection.cursor()
            cur.execute('''DELETE FROM admin where admin_id = %s and password = %s;''',(admin_id,password))
            mysql.connection.commit()
    except:
        #print admin_id,password
        print ('bad')
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM admin''')
    data = cur.fetchall()
    return render_template('admin-add.html', data = data)

@app.route('/addfacilities', methods=['GET', 'POST'])
def addfacilities():
    try:
        if request.method == 'POST':
            sid = request.form['bid']
            fac = request.form['fac']
            cur = mysql.connection.cursor()
            cur.execute('''INSERT INTO facility(sid, facility) VALUES (%s, %s)''', (sid, fac))
            mysql.connection.commit()
    except:
        print('bad')

    cur = mysql.connection.cursor()
    cur.execute('''SELECT s.name, f.facility 
                    FROM facility f 
                    JOIN society s 
                    ON s.sid = f.sid''')
    query_result = cur.fetchall()

    data = {}
    for community, facility in query_result:
        if community in data:
            data[community].append(facility)
        else:
            data[community] = [facility]


    cur.execute('''SELECT sid, name FROM society''')
    society_list = cur.fetchall()

    return render_template('admin-facilities-insert.html', data=data.items(), society_list=society_list)


@app.route('/communityadd', methods=['POST','GET'])
def communityadd():
    if request.method == 'POST':
        sid = request.form['bid']
        name = request.form['name']
        address = request.form['address']
        mgr = request.form['mgr_per_id']
        image = request.files['image']
        if image:
          image.save(os.path.join('static/communities', image.filename))

        cur = mysql.connection.cursor()
        try:
            cur.execute('''INSERT into society(sid,name,address,mgr_per_id,img) 
            	VALUES (%s,%s,%s,%s,%s)''',(sid,name,address,mgr,image.filename))
            mysql.connection.commit()
        except:
            print ('bad')
            print (sid)
    cur = mysql.connection.cursor()
    cur.execute('''SELECT s.sid, s.name, s.address, p.name 
                   FROM society s
                   JOIN person p ON s.mgr_per_id = p.per_id''')
    data = cur.fetchall()

    cur = mysql.connection.cursor()
    cur.execute('''SELECT per_id, name FROM person''')
    persons = cur.fetchall()

    return render_template('admin-community-insert.html', data = data, persons=persons)


@app.route('/communityupdate', methods=['GET', 'POST'])
def communityupdate():
    try:
        if request.method == 'POST':
            sid = request.form['bid']
            mgr = request.form['mgr_per_id']
            cur = mysql.connection.cursor()
            cur.execute('''UPDATE society SET mgr_per_id = %s WHERE sid = %s''', (mgr, sid))
            mysql.connection.commit()
    except:
        print('bad')
        # print sid, mgr

    cur = mysql.connection.cursor()
    cur.execute('''SELECT per_id, name FROM person''')
    persons = cur.fetchall()

    cur.execute('''SELECT s.sid, s.name, s.address, p.name 
                   FROM society s
                   JOIN person p ON s.mgr_per_id = p.per_id''')
    data = cur.fetchall()
    
    return render_template('admin-comunity-update.html', data=data, persons=persons)


@app.route('/addperson', methods=['POST','GET'])
def addperson():
    if request.method == 'POST':
        per_id = request.form['per_id']
        name = request.form['name']
        phone = request.form['phone']
        cur = mysql.connection.cursor()
        try:
            cur.execute('''INSERT into person(per_id,name,phone) VALUES (%s,%s,%s)''',(per_id,name,phone))
            mysql.connection.commit()
        except:
            print ('bad')
            #print per_id
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM person''')
    data = cur.fetchall()
    return render_template('add-person.html', data = data)

@app.route('/login/<build>', methods = ['GET', 'POST'])
# we can make another function for login which returns true if user exist
# in the db.
def user_login(build):
    apt_id = str(build)
    cur = mysql.connection.cursor()
    cur.execute('''Select status,sid from apartment where apt_id = %s''',(apt_id,))
    stat = cur.fetchall()
    sid = stat[0][1]
    if(stat[0][0] == 'n'):
        flash('The chosen apartment is unavailable, please book another apartment.',(apt_id,))
        return redirect(url_for('home'))
    else:
        if request.method == 'POST':
            user_email = request.form['user_id']
            user_password = request.form['user_pwd']
            cur = mysql.connection.cursor()
            cur.execute('''SELECT * FROM user WHERE (email, password) = (%s,%s)''',(user_email,user_password))
            n = cur.fetchall()


            cur = mysql.connection.cursor()
            cur.execute('''SELECT name FROM user WHERE (email, password) = (%s,%s)''',(user_email,user_password))
            name = cur.fetchall()
            print("--------name is ----------")
            print(name[0][0])
            print("------------------")
            name=name[0][0]

            cur = mysql.connection.cursor()
            cur.execute('''SELECT uid FROM user WHERE (email, password) = (%s,%s)''',(user_email,user_password))
            uid = cur.fetchall()
            print("--------uid is ----------")
            print(uid[0][0])
            print("------------------")
            uid=uid[0][0]
            session['name'] = name
            session['email'] = user_email
            session['password'] = user_password
            session['uid'] = uid

            if len(n)!=0:
                user_id = str(n[0][0])
                try:
                    cur = mysql.connection.cursor()
                    #cur.execute('''UPDATE apt_book SET uid = %s, book_date = CURDATE() WHERE apt_id = %s''',(user_id,apt_id,))
                    cur.execute('''INSERT INTO apt_book(apt_id,sid,uid,book_date) 
                        VALUES (%s,%s,%s,NOW())''',(apt_id,sid,user_id,))
                    mysql.connection.commit()
                    print (traceback.print_exc())
                    flash('Your Apartment has been booked successfully.', 'success')  # Set the flash message

                    cur = mysql.connection.cursor()
                    cur.execute('''SELECT a.doorno, s.name, ab.booking_id, a.price, ab.book_date FROM apt_book ab
                    JOIN user u ON u.uid = ab.uid
                    JOIN society s ON s.sid = ab.sid
                    JOIN apartment a ON a.apt_id = ab.apt_id
                    WHERE u.uid = %s
                    ORDER BY ab.booking_id DESC''', (uid,))
                    data = cur.fetchall()
                    return render_template('user-dashboard.html',name=session['name'],username=session['email'],uid=session['uid'],data=data)
                except:
                     print (traceback.print_exc())
                     flash('An error occurred while booking the apartment. Please try again.', 'error')
                return redirect('user-dashboard',name=session['name'],username=session['email'],uid=session['uid'],data=data) 
            else:
                 flash('Invalid username/password.Try again or Sign up.')
    return render_template('login.html')

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    is_id_uniq = False
    if request.method == 'POST':
        user_name = request.form['user_name']
        #uid = request.form['uid']
        user_id = request.form['user_id']
        user_password = request.form['user_pwd']
        cur = mysql.connection.cursor()
        try:
            # uid is auto increment
            cur.execute('''INSERT INTO user (name, email, password) 
                VALUES (%s, %s, %s)''', (user_name, user_id, user_password))
            n = cur.fetchall()
            mysql.connection.commit()
            flash('User added! Sign in to book your apartment.')
            return redirect(url_for('home'))
        except Exception as e:
            print (traceback.print_exc())
            flash("E-mail id already exist")
    return render_template('signup.html')

@app.route('/adddetails', methods = ['GET','POST'])
def adddetails():
    if request.method == 'POST':
        adc = request.form['apt_detail_code']
        bhk = request.form['bhk']
        bathroom = request.form['bathroom']
        size = request.form['size']
        desc = request.form['desc']
        try:
            cur = mysql.connection.cursor()
            cur.execute('''INSERT INTO apt_detail(apt_detail_code,bhk,bathroom,size,description) 
                VALUES (%s,%s,%s,%s,%s)''',(adc,bhk,bathroom,size,desc,))
            mysql.connection.commit()
        except:
            print (traceback.print_exc())
    cur = mysql.connection.cursor()
    cur.execute('''SELECT * FROM apt_detail''')
    data = cur.fetchall()
    return render_template('add-details.html',data = data)

@app.route('/transcript')
def transcript():
    cur = mysql.connection.cursor()
    cur.execute('''SELECT a.doorno,s.name,ab.booking_id,u.name, ab.book_date FROM apt_book ab
                JOIN user u ON u.uid=ab.uid
                JOIN society s ON s.sid= ab.sid
                JOIN apartment a ON a.apt_id = ab.apt_id''')
    data = cur.fetchall()
    #print data
    return render_template('transcript.html', data = data)

@app.route('/login',methods = ['GET','POST'])
def login():
    return render_template('login.html')  
'''
@app.route('/authenticate',methods = ['GET','POST'])
def authenticate():
    if request.method == 'POST':
        apt_id = request.form['apt']
        uid = request.form['uid']
        name = request.form['name']
        try:
            cur = mysql.connection.cursor()
            # need to create a new per_id(cuz it might clash with already existing ids)
            # check if the user already exist in person table
            # if doesnt insert new values else dont insert
            # using auto increment for per_id
            cur.execute("INSERT INTO person(per_id,name) VALUES (%s,%s)",(uid,name,))
            mysql.connection.commit()
            cur.execute("UPDATE apartment SET owner_per_id = %s, status = 'n' WHERE apt_id = %s",(uid,apt_id))
            mysql.connection.commit()
        except:
            print traceback.print_exc()
    cur = mysql.connection.cursor()
    cur.execute("SELECT apt_id,a.uid,u.uid,u.name FROM apt_book a,user u GROUP BY apt_id,a.uid,u.name HAVING MAX(book_date) and u.uid = a.uid")
    data = cur.fetchall()
    return render_template('approve.html',data = data)
'''

@app.route('/updapt', methods=['GET', 'POST'])
def updapt():
    try:
        if request.method == 'POST':
            apt_id = request.form['apt_id']
            status = request.form['status']
            sid = request.form['sid']
            owner_id = request.form['owner_id']
            cur = mysql.connection.cursor()
            cur.execute('''UPDATE apartment SET sid=%s, owner_per_id=%s, status = %s 
                            WHERE apt_id = %s''', (sid, owner_id, status, apt_id))
            mysql.connection.commit()
    except:
        print('bad')
        print(traceback.print_exc())

    cur = mysql.connection.cursor()
    cur.execute('''SELECT apt.apt_id,apt.doorno, soc.name, per.name, apt.status 
                   FROM apartment apt
                   LEFT JOIN society soc ON apt.sid = soc.sid
                   LEFT JOIN person per ON apt.owner_per_id = per.per_id''')
    data = cur.fetchall()

    # Fetch data for the "society" table to populate the dropdown list
    cur.execute('''SELECT sid, name FROM society''')
    society_data = cur.fetchall()
    # Fetch data for the "person" table to populate the dropdown list
    cur.execute('''SELECT per_id, name FROM person''')
    owner_data = cur.fetchall()

    return render_template('admin-apartment-update.html', data=data, society_data=society_data, owner_data=owner_data)

@app.route('/booking_history/<int:uid>')
def booking_history(uid):
    cur = mysql.connection.cursor()
    cur.execute('''SELECT a.doorno, s.name, ab.booking_id, u.name, ab.book_date FROM apt_book ab
                JOIN user u ON u.uid = ab.uid
                JOIN society s ON s.sid = ab.sid
                JOIN apartment a ON a.apt_id = ab.apt_id
                WHERE u.uid = %s''', (uid,))
    data = cur.fetchall()
    return render_template('booking_history.html', data=data)



# Chat messages get appended here
items = []

@app.route("/new_item", methods=["POST"])
def add():
    userPosted = session['name']
    message = request.form["one"]
    newLine = userPosted + ": " + message

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO messagelog (userName,userSent, roomName, message) VALUES (%s,%s, %s, %s)", (session['name'],session['email'], session['chatroom'], message))
    mysql.connection.commit()
    cur.close()

    items.append([newLine])
    return jsonify(items)

@app.route("/items")
def get_items():
    return jsonify(items)

# By default, redirect to login
@app.route("/messages")
def messages():
    return redirect(url_for("login_room"))

@app.route("/login_room/", methods=["GET", "POST"])
def login_room():
    error = None

    if request.method == "POST":
        email = request.form["user"]
        password = request.form["pass"]
        print("------------------------")
        print(email)
        print(password)
        print("--------^^^^^^^^^^---")
        if not email:
            error = 'Please enter an email.'
        elif not password:
            error = 'Please enter a password.'

        if error is None:
            print("NOOOOOO Errors ---")
            user = User.query.filter_by(email=email).first()

            if user is None:
                error = 'Please enter a valid email.'

            if error is None:
                if not user.password == password:
                    error = 'Incorrect password.'

            if error is None:
                session['email'] = email
                session['name'] = user.name 
                flash("Login Success!")
                return redirect(url_for("chathomePage"))

            flash(error)
            return redirect(url_for("login_room"))

        flash(error)

    return render_template('login_room.html')

@app.route('/delete_room/<room_name>')
def deleteEvent(room_name):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM chatroom WHERE roomName=%s", (room_name,))
    cur.execute("DELETE FROM messagelog WHERE roomName=%s", (room_name,))
    mysql.connection.commit()
    cur.close()
    
    items.clear()
    flash('Room and associated messages successfully deleted.')
    return redirect(url_for("chathomePage"))
items=[]

@app.route('/chat/<room_name>', methods=["GET", "POST"])
def room(room_name):
    items.clear()

    session['chatroom'] = room_name

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM messagelog WHERE roomName=%s ORDER BY id ASC", (room_name,))
    chatLog = cur.fetchall()
    cur.close()

    for item in chatLog:
        user = item['userName']
        message = item['message']
        completeString = user + ": " + message
        items.append([completeString])

    
    return render_template('rooms.html', email=session['email'], roomName=room_name, messages=items)





@app.route("/chathomePage", methods=["GET", "POST"])
def chathomePage():
    error = None
    if request.method == "POST":
        name = request.form["roomName"]

        if not name:
            error = 'Please enter a valid room name.'

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM chatroom WHERE roomName=%s", (name,))
        checkConflict = cur.fetchone()
        cur.close()

        if checkConflict:
            error = 'Naming conflict: chatroom with this name already exists. Please rename and try again.'

        if error is None:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO chatroom (roomName, userCreated) VALUES (%s, %s)", (name, session['email']))
            mysql.connection.commit()
            cur.close()

            flash("New room created.")
            return redirect(url_for("chathomePage"))

        flash(error)

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM chatroom ORDER BY id ASC")
    chatRooms = cur.fetchall()
    cur.close()

    return render_template('chathomePage.html', email=session['email'], rooms=chatRooms,name=session['name'],username=session['email'])

@app.route("/new/", methods=["GET", "POST"])
def registerUser():
    if request.method == "POST":
        error = None
        name = request.form["newname"]
        email = request.form["newcustomer"]
        password = request.form["newpass"]
        session['name'] = name
        if not name:
            error = 'Name is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        print("-----------in new-------------")
        print(name)
        print(email)
        print(password)
        print("------------------------")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            error = 'This email already exists.'

        if error is None:
            cur = mysql.connection.cursor()
            affected_rows = cur.execute("INSERT INTO user (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
            mysql.connection.commit()

            # Print all records after insertion
            cur.execute("SELECT * FROM user")
            all_users = cur.fetchall()
            for user in all_users:
                print(user)

            cur.close()

            flash("New user account created.")
            return redirect(url_for("login_room"))

        flash(error)
        return redirect(url_for("registerUser"))

    return render_template('register.html')





    

# Logout page
@app.route("/logout/")
def logout():
    session.clear()
    flash('User logged out.')
    return redirect(url_for("login_room"))

if __name__ == "__main__":
    # Create the database tables if they don't exist
    with app.app_context():
        db.create_all()

    app.run()