import psycopg2
from flask import Flask, render_template, redirect, url_for, request


def connect():
    conn = psycopg2.connect(
    host="localhost",
    database="dbmsproject",
    user="postgres",
    password = "admin123"
   )
    conn.autocommit = True
    return conn

con = connect().cursor()


app = Flask(__name__,template_folder='templates')



# use decorators to link the function to a url
@app.route('/')
def home():
    return "Hello, World!"  # return a string

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
	
	error = None
	if request.method == 'POST':
		con.execute("SELECT * FROM users where username = %s and password = %s ;",(request.form['username'],request.form['password']))
		x = con.fetchall()
		if len(x)<=0:
			error = 'Invalid Credentials. Please try again.'
		else:
			return redirect(url_for('welcome'))
	return render_template('login.html', error=error)

@app.route('/admin_login',methods = ['GET','POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form['username'] == 'Admin':
            if request.form['password']=="admin123":
                return render_template('hotel_add_del.html')
            else:
                error = 'Invalid Credentials. Please try again.'
        else:
            error = 'Invalid Credentials. Please try again.'
    # error = 'Invalid Credentials. Please try again.'
    return render_template('admin.html',error = error)

@app.route('/register', methods=['GET', 'POST'])
def register():	
	error = None
	if request.method == 'POST':
		usern = request.form['username']
		print(usern)
		con.execute("SELECT * FROM users where username = '%s';"%(request.form['username']))
		x = con.fetchall()
		if len(x)>0:
			error = 'Username already exists.'
		else:
			con.execute("select * from users;")
			nextId = 1
			if(not(len(con.fetchall())==0)):	
				con.execute("select max(userid) from users;")
				nextId = con.fetchall()[0][0] + 1
			con.execute("insert into users values (%s,%s,%s,%s,%s,%s,%s,0);",(nextId,request.form['username'],request.form['password'],request.form['name'],request.form['address'],request.form['email'],request.form['phone']))
	

			return redirect(url_for('welcome'))
	return render_template('register.html', error=error)
   
@app.route('/hotel_add_del',methods = ['GET','POST'])
def hotel_add_del():
    error = None
    if request.method == 'POST':
        hotelname = request.form['hotelname']
        print(hotelname)
        con.execute("select * from hotel_detail where hotelname = '%s';"%(request.form['hotelname']))
        x = con.fetchall()
        if len(x)>0:
            error = 'Hotel is already added in the list.'
        else:
            con.execute("select * from hotel_detail;")
            nextId = 1
            if(not(len(con.fetchall())==0)):
                con.execute("select max(hotelid) from hotel_detail;")
                nextId = con.fetchall()[1][0] + 1
            con.execute("insert into hotel_detail values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",('0',nextId,request.form['hotelname'],request.form['address'],request.form['city'],request.form['country'],request.form['zipcode'],request.form['propertytype'],request.form['starrating'],request.form['latitude'],request.form['longitude'],request.form['source'],request.form['url'],request.form['curr']))

            return redirect(url_for('welcome'))
    return render_template('hotel_add_del.html',error=error)


@app.route('/show_hotels', methods=['GET', 'POST'])
def show():	
    
	error = 0
	data = {}

	con.execute("SELECT DISTINCT country from hotel_detail order by country ;")
	#data['country'] = con.fetchall()
	result = []
	for i in con.fetchall():
		result.extend(i)
	data['country'] = result

	
	if len(data['country'])<=0:
		error = 1

	if request.method == 'POST':
#		op1 = request.form.get('option1')
#		op2 = request.form.get('option2')    		
    		
		print(request.form['country'],)
		if not(request.form['country']=="Choose Country") and not(request.form['city']==""):
			con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['country'],request.form['city']))
    		
		elif not(request.form['country']=="Choose Country"):
			con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country']))	
			print(request.form.get('country'))
			print(con.mogrify("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country'])))
		else:
			con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where city = '%s' LIMIT 10 ;"%request.form['city'])
    		
		data['data'] = con.fetchall()
		if len(data['data'])<=0:
			error = 1
    	
	data['error'] = error
    	
	#print(data)
	return render_template('show_hotels.html', data=data)

@app.route('/hotel/<int:hotelid>', methods=['GET', 'POST'])
def hotel(hotelid):	
    #return "Hotel:" + str(hotelid)
	error = 0
	data = {}

	con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s ;" %(str(hotelid)))
	#data['country'] = con.fetchall()
	
	data['rooms'] = con.fetchall()
	print(data['rooms'])

	if len(data['rooms']) <= 0:
		error = 1
	
	data['error'] = error

	return render_template('room_details.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)

