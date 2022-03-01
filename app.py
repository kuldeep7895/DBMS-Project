from crypt import methods
import psycopg2
import random
from flask import Flask, render_template, redirect, url_for, request,session
from datetime import datetime,timezone
##########################
def captcha_str():
	var_list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
			'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z',
			'1','2','3','4','5','6','7','8','9','0']
	capt = ''
	for i in range(6):
		n = random.randint(0,len(var_list)-1)
		capt = capt + var_list[n]
	return capt

capt_arr = []
hotelname_arr =[]
hotelid_arr = []
##########################

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
app.secret_key = "secret"


# use decorators to link the function to a url
@app.route('/')
def home():
    return redirect('/welcome')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


# Route for handling the login page logic
@app.route('/user_login', methods=['GET', 'POST'])
def login():
	
	error = None
	if request.method == 'POST':
		con.execute("SELECT * FROM users where username = %s and password = %s LIMIT 1 ;",(request.form['username'],request.form['password']))
		x = con.fetchall()
		if len(x)<=0:
			error = 'Invalid Credentials. Please try again.'
		else:
			session['username'] = request.form['username']
			#return redirect(url_for('welcome'))
			return redirect(url_for('user_dashboard'))
	return render_template('login.html', error=error)

@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():	
    
	error = 0
	bookings_empty = 0
	data = {}
	data['username'] = session['username']
	con.execute("SELECT userid, username, name, address, email, phone, walletbalance FROM users where username = '%s';" %(data['username']))

	data['user_details'] = con.fetchall()[0]
	userid = data['user_details'][0]

	con.execute("with table1 as ( select hotelid, roomid, fromdate, todate, created_at from bookings where userid = %s ) select hotelname, address, city, country, room_detail.roomamenities, onsiterate, fromdate, todate, created_at, table1.hotelid, table1.roomid from ((table1 inner join hotel_detail on hotel_detail.hotelid = table1.hotelid) inner join room_price on room_price.id = table1.roomid) inner join room_detail on room_detail.id = table1.roomid ;" %(str(userid)))
	data['bookings'] = con.fetchall()

	if len(data['bookings']) <= 0:
		bookings_empty = 1

	print(data['bookings'])
	
	data['bookings_empty'] = bookings_empty

	return render_template('user_dashboard.html', data=data)

@app.route('/edit_user_detail', methods=['GET', 'POST'])
def edit_user_detail():	
    
	error = 0
	bookings_empty = 0
	data = {}
	username = session['username']

	if request.method == "POST":
		con.execute("update users set password='%s', name='%s', address='%s', email='%s', phone=%s where username='%s'" %(request.form['password'],request.form['name'],request.form['address'],request.form['email'],request.form['phone'], username))		
		

		return redirect(url_for('user_dashboard'))
	
	con.execute("SELECT username, name, address, email, phone, walletbalance FROM users where username = '%s';" %(username))
	data = con.fetchall()

	return render_template('edit_user_detail.html', data=data)

@app.route('/admin_login',methods = ['GET','POST'])

########################################################3
def admin_login():
	capt = captcha_str()
	capt_arr.append(capt)
	# capt_index+=1
	error = None
	if request.method == 'POST':
		print(request.form['captcha'])
		print()
		print(capt)
		print(capt_arr)
		# print(capt_index)
		if request.form['username']=='Admin':
			if request.form['password']=='admin123':
				if request.form['captcha']==capt_arr[len(capt_arr)-2]:
					return redirect(url_for('admin_page'))
				else:
					error = 'Captcha did not match'
			else:
				error = 'Incorrect Password'
		else:
			error = 'Incorrrect Username'
	return render_template('admin.html',capt = capt,error = error)
########################################################################

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

@app.route('/reviews/<int:hotelid>', methods=['GET', 'POST'])
def review(hotelid):
	error = 0
	data = {}

	con.execute("select reviews from reviews where hotelid = %s order by reviews ;" %(str(hotelid)))
	result = []
	for i in con.fetchall():
		result.extend(i)
	data['review'] = result

	con.execute("select max(reviewid) + 1 from reviews ;")
	reviewid = con.fetchall()[0][0]

	if reviewid is None:
		reviewid = 1

	if request.method == 'POST':
		if not(request.form.get('newreview') == ""):
			con.execute("select userid from users where username = '%s' ;" %(session['username']))
			userid = con.fetchall()[0][0]

			con.execute("insert into reviews (reviewid, userid, hotelid, reviews) values( %s, %s, %s, '%s' );" %(str(reviewid), str(userid), str(hotelid), request.form.get('newreview')))
			return redirect('/user_dashboard')
	return render_template('hotel_reviews.html', data=data, error=error)

###############################################################
@app.route('/admin_page',methods=['GET','POST'])
def admin_page():
	con.execute("select count(hotelid) as number from hotel_detail;")
	num = con.fetchall()[0][0]
	con.execute("select count(distcity) as count from (  select distinct(city) as distcity  from hotel_detail group by city) as temp;")
	city = con.fetchall()[0][0]
	con.execute("select count(distcity) as count from (  select distinct(country) as distcity  from hotel_detail group by country) as temp;")
	country = con.fetchall()[0][0]
	return render_template("admin_page.html",num = num,city = city, country = country)

@app.route('/add_hotel',methods=['GET','POST'])
def add_hotel():
	error = None
	check = -1
	
	if request.method=='POST':
		hotelname = request.form['hotelname']
		hotelname_arr.append(hotelname)
		if len(hotelname)==0:
			check = 0
		else:
			con.execute("select * from hotel_detail where hotelname = '%s';"%(hotelname))
			search_res = con.fetchall()
			if len(search_res)==0:
				check = 1
			else:
				check=0
			
	
	return render_template('add_hotel.html',check= check)

@app.route('/add_hotel1',methods=['GET','POST'])
def add_hotel1():
	shift = None
	error = None
	hotel_name = hotelname_arr[len(hotelname_arr)-1]
	# print("hotelname")
	# print(hotelname_arr)
	if request.method == 'POST':
		# print("asfa")
		con.execute("select * from hotel_detail;")
		# print("b")
		nextId = 1
		id = 1
		if(not(len(con.fetchall())==0)):
			# print("c")
			con.execute("select max(hotelid) from hotel_detail;")
			# print("d")
			nextId = con.fetchall()[0][0] + 1
			con.execute("select max(id) from hotel_detail;")
			id = con.fetchall()[0][0]+1
			# print(nextId)
			# print(id)
			hotelid_arr.append(nextId)
		if not(request.form['address']=="") and not(request.form['city']=="") and not(request.form['country']=="") and not(request.form['zipcode']=="") and not(request.form['propertytype']=="") and not(request.form['starrating']=="") and not(request.form['url']=="") and not(request.form['currency']==""):
			con.execute("insert into hotel_detail values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(id,nextId,hotel_name,request.form['address'],request.form['city'],request.form['country'],request.form['zipcode'],request.form['propertytype'],request.form['starrating'],0.0,0.0,0,request.form['url'],request.form['currency']))
			shift = 1
		else:
			error = 1
		# con.execute("insert into hotel_detail values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);",(id,nextId,hotel_name,request.form['address'],request.form['city'],request.form['country'],request.form['zipcode'],request.form['propertytype'],request.form['starrating'],0.0,0.0,0,request.form['url'],request.form['currency']))
		# shift = 1
	return render_template("add_hotel1.html",hotelname = hotel_name,shift = shift,error = error)

@app.route('/del_hotel',methods=['GET','POST'])
def del_hotel():
	error = 0
	data = {}

	con.execute("SELECT DISTINCT country from hotel_detail order by country ;")
	result = []
	for i in con.fetchall():
		result.extend(i)
	data['country'] = result

	
	if len(data['country'])<=0:
		error = 1

	if request.method == 'POST':   		
    		
		print(request.form['country'],)
		if not(request.form['hotelname']==""):
			if not(request.form['country']=="Choose Country") and not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['country'],request.form['city']))
				
			elif not(request.form['country']=="Choose Country"):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and country = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['country']))	
			elif not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and city = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['city']))
			else:
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' LIMIT 10 ;"%(request.form['hotelname']))
		else:
			if not(request.form['country']=="Choose Country") and not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['country'],request.form['city']))
				
			elif not(request.form['country']=="Choose Country"):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country']))	
			else:
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where city = '%s' LIMIT 10 ;"%request.form['city'])
    		
		data['data'] = con.fetchall()
		if len(data['data'])<=0:
			error = 1
    	
	data['error'] = error
    	
	#print(data)
	return render_template('del_hotel.html', data=data)

@app.route('/del_hotel1/<int:hotelid>',methods=['GET','POST'])
def del_hotel1(hotelid):
	print(hotelid)
	con.execute("DELETE FROM hotel_detail WHERE hotelid = '%s';"%hotelid)
	return render_template('del_hotel1.html')

@app.route('/edit_hotel',methods=['GET','POST'])
def edit_hotel():
	error = 0
	data = {}
	con.execute("SELECT DISTINCT country from hotel_detail order by country ;")
	result = []
	for i in con.fetchall():
		result.extend(i)
	data['country'] = result
	if len(data['country'])<=0:
		error = 1
	if request.method == 'POST':   		
		if not(request.form['hotelname']==""):
			if not(request.form['country']=="Choose Country") and not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['country'],request.form['city']))
				
			elif not(request.form['country']=="Choose Country"):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and country = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['country']))	
			elif not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' and city = '%s' LIMIT 10 ;"%(request.form['hotelname'],request.form['city']))
			else:
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where hotelname = '%s' LIMIT 10 ;"%(request.form['hotelname']))
		else:
			if not(request.form['country']=="Choose Country") and not(request.form['city']==""):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['country'],request.form['city']))
				
			elif not(request.form['country']=="Choose Country"):
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country']))	
			else:
				con.execute("SELECT hotelid, hotelname, address, city, country FROM hotel_detail where city = '%s' LIMIT 10 ;"%request.form['city'])
    		
		data['data'] = con.fetchall()
		if len(data['data'])<=0:
			error = 1
    	
	data['error'] = error
	return render_template('edit_hotel.html', data=data)

@app.route('/edit_hotel1/<int:hotelid>',methods=['GET','POST'])
def edit_hotel1(hotelid):
	shift = None
	con.execute("SELECT hotelname FROM hotel_detail WHERE hotelid = '%s';"%(hotelid))
	hotel_name = con.fetchall()[0][0]
	if request.method == "POST":
		if not(request.form['address']==""):
			con.execute("UPDATE hotel_detail SET address = '%s' WHERE hotelid = '%s';"%(request.form['address'],hotelid))
		
		if not(request.form['city']==""):
			con.execute("UPDATE hotel_detail SET city = '%s' WHERE hotelid = '%s';"%(request.form['city'],hotelid))
		
		if not(request.form['country']==""):
			con.execute("UPDATE hotel_detail SET country = '%s' WHERE hotelid = '%s';"%(request.form['country'],hotelid))
		
		if not(request.form['zipcode']==""):
			con.execute("UPDATE hotel_detail SET zipcode = '%s' WHERE hotelid = '%s';"%(request.form['zipcode'],hotelid))
		
		if not(request.form['propertytype']==""):
			con.execute("UPDATE hotel_detail SET propertytype = '%s' WHERE hotelid = '%s';"%(request.form['propertytype'],hotelid))
		
		if not(request.form['starrating']==""):
			con.execute("UPDATE hotel_detail SET starrating = '%s' WHERE hotelid = '%s';"%(request.form['starrating'],hotelid))
		
		if not(request.form['url']==""):
			con.execute("UPDATE hotel_detail SET url = '%s' WHERE hotelid = '%s';"%(request.form['url'],hotelid))
		
		if not(request.form['currency']==""):
			con.execute("UPDATE hotel_detail SET curr = '%s' WHERE hotelid = '%s';"%(request.form['currency'],hotelid))
		shift = 1
	return render_template("edit_hotel1.html",hotelname = hotel_name,shift = shift,hotelid = hotelid)
		
@app.route('/add_hotel_more',methods=['GET','POST'])
def add_hotel_more():
	shift = None
	error = None
	hotel_name = hotelname_arr[len(hotelname_arr)-1]
	print(hotelname_arr)
	print(hotelid_arr)
	# print("hotelname")
	# print(hotelname_arr)
	con.execute("select")
	if request.method == 'POST':
		if not(request.form['min_price']=="") and not(request.form['max_price']=="") and not(request.form['Diff_min_price']=="") and not(request.form['Diff_max_price']=="") and not(request.form['score']==""):
			con.execute("insert into hotel_price values(%s,%s,%s,%s,%s,%s);",(hotelid_arr[len(hotelid_arr)-1],request.form['min_price'],request.form['max_price'],request.form['Diff_min_price'],request.form['Diff_max_price'],request.form['score']))
			shift = 1
		else:
			error = 1
	return render_template("add_hotel_more.html",hotelname = hotel_name,shift = shift,error = error)

@app.route('/edit_hotel_more/<int:hotelid>',methods=['GET','POST'])
def edit_hotel_more(hotelid):
	print(hotelid)
	shift = None
	con.execute("SELECT hotelname FROM hotel_detail WHERE hotelid = '%s';"%(hotelid))
	hotel_name = con.fetchall()[0][0]
	if request.method == "POST":
		if not(request.form['min_price']==""):
			con.execute("UPDATE hotel_price SET min = '%s' WHERE hotelcode = '%s';"%(request.form['min_price'],hotelid))
		
		if not(request.form['max_price']==""):
			con.execute("UPDATE hotel_price SET max = '%s' WHERE hotelcode = '%s';"%(request.form['max_price'],hotelid))
		
		if not(request.form['Diff_min_price']==""):
			con.execute("UPDATE hotel_price SET diff_min = '%s' WHERE hotelcode = '%s';"%(request.form['Diff_min_price'],hotelid))
		
		if not(request.form['Diff_max_price']==""):
			con.execute("UPDATE hotel_price SET diff_max = '%s' WHERE hotelcode = '%s';"%(request.form['Diff_max_price'],hotelid))
		
		if not(request.form['score']==""):
			con.execute("UPDATE hotel_price SET score = '%s' WHERE hotelcode = '%s';"%(request.form['score'],hotelid))
		shift = 1
	return render_template('edit_hotel_more.html',hotelname = hotel_name,shift = shift)

@app.route('/user_management',methods=['GET','POST'])
def user_management():
	error = None
	return render_template('user_management.html')

@app.route('/del_user',methods=['GET','POST'])
def del_user():
	erroru = None
	errorno = None
	errorp = None
	errornp = None
	success = None
	if request.method == "POST":
		username  = ""
		if(request.form['username']==""):
			errorno = 1
		else:
			con.execute("SELECT userid, password from users WHERE username = '%s';"%(request.form['username']))
			user_row = con.fetchall()
			if(len(user_row)<=0):
				erroru = 1
			else:
				userid = user_row[0][0]
				password = user_row[0][1]
				if(request.form['password']==""):
					errornp = 1
				else:
					if(request.form['password']==password):
						con.execute("DELETE FROM users WHERE userid = '%s';"%(userid))
						con.execute("DELETE FROM bookings WHERE userid = '%s';"%(userid))
						con.execute("DELETE FROM reviews WHERE userid = '%s';"%(userid))
						success = 1
					else:
						errorp = 1
	return render_template('del_user.html',erroru = erroru,errornu = errorno,errorp = errorp,errornp = errornp,success = success)

@app.route('/del_booking',methods=['GET','POST'])
def del_booking():
	error = None
	erroru = None
	errorno = None
	errorp = None
	errornp = None
	success = None
	data = {}
	if request.method == "POST":
		username  = ""
		if(request.form['username']==""):
			errorno = 1
		else:
			con.execute("SELECT userid, password from users WHERE username = '%s';"%(request.form['username']))
			user_row = con.fetchall()
			if(len(user_row)<=0):
				erroru = 1
			else:
				userid = user_row[0][0]
				password = user_row[0][1]
				if(request.form['password']==""):
					errornp = 1
				else:
					if(request.form['password']==password):
						con.execute("SELECT * FROM bookings WHERE userid = '%s';"%(userid))
						data['data'] = con.fetchall()
						success = 1
					else:
						errorp = 1
	return render_template('del_booking.html',error = error, data = data)

@app.route('/delete_page/<int:id>/<int:is_booking>',methods=['GET','POST'])
def delete_page(id,is_booking):
	if(is_booking==1):
		con.execute("DELETE FROM bookings WHERE bookingid = '%s';"%(id))
	else:
		con.execute("DELETE FROM reviews WHERE reviewid = '%s';"%(id))
	return render_template("delete_page.html")

@app.route('/hrm',methods=['GET','POST'])
def hrm():
	error = None
	erroru = None
	errorno = None
	errorp = None
	errornp = None
	success = None
	data = {}
	if request.method == "POST":
		username  = ""
		if(request.form['username']==""):
			errorno = 1
		else:
			con.execute("SELECT userid, password from users WHERE username = '%s';"%(request.form['username']))
			user_row = con.fetchall()
			if(len(user_row)<=0):
				erroru = 1
			else:
				userid = user_row[0][0]
				password = user_row[0][1]
				if(request.form['password']==""):
					errornp = 1
				else:
					if(request.form['password']==password):
						con.execute("SELECT * FROM reviews WHERE userid = '%s';"%(userid))
						data['data'] = con.fetchall()
						success = 1
					else:
						errorp = 1
	return render_template('hrm.html',error = error, data = data)
###############################################################

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
	error = 0
	data = {}

	con.execute("SELECT DISTINCT roomamenities from room_detail where hotelcode = %s ;" %(str(hotelid)))
	result = []
	for i in con.fetchall():
		result.extend(i)
	data['ra'] = result

	if request.method == 'POST':
		print(request.form.get('ra'))

		if not(request.form.get('ra')=="Choose Room Amenities") and not(request.form['startprice']=="" or request.form['startprice']==None) and not(request.form['endprice']=="" or request.form['endprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.roomamenities = '%s' and onsiterate between %s and %s ;" %(str(hotelid), request.form.get('ra'), request.form['startprice'], request.form['endprice']))		

		elif not(request.form.get('ra')=="Choose Room Amenities") and not(request.form['startprice']=="" or request.form['startprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.roomamenities = '%s' and  onsiterate >= %s ;" %(str(hotelid), request.form.get('ra'), str(request.form['startprice'])))

		elif not(request.form.get('ra')=="Choose Room Amenities") and not(request.form['endprice']=="" or request.form['endprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.roomamenities = '%s' and  onsiterate <= %s ;" %(str(hotelid), request.form.get('ra'), str(request.form['endprice'])))

		elif not(request.form['startprice']=="" or request.form['startprice']==None) and not(request.form['endprice']=="" or request.form['endprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and onsiterate between %s and %s ;" %(str(hotelid), str(request.form['startprice'], str(request.form['endprice']))))		

		elif not(request.form.get('ra')=="Choose Room Amenities"):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.roomamenities = '%s' ;" %(str(hotelid), request.form.get('ra')))
			#print(con.mogrify("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.roomamenities = '%s' ;" %(str(hotelid), request.form.get('ra'))))

		elif not(request.form['startprice']=="" or request.form['startprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and onsiterate >= %s ;" %(str(hotelid), request.form['startprice']))

		elif not(request.form['endprice']=="" or request.form['endprice']==None):
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and onsiterate <= %s ;" %(str(hotelid), request.form['endprice']))

		else:
			con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s ;" %(str(hotelid)))

	else:
		con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s ;" %(str(hotelid)))
		#data['country'] = con.fetchall()
		
	result = con.fetchall()
	#print(data['rooms'])
	data['rooms'] = []
	if len(result) <= 0:
		error = 1

	else:
		for x in result:
			temp = list(x)
			if temp[1] is not None:
				temp[1] = temp[1].split(": ;")
				temp[1].pop(-1)
				data['rooms'].append(temp)

		
		
	data['error'] = error

	return render_template('room_details.html', data=data)

#@app.route('/pay', methods=['GET', 'POST'])
#def pay():
#	return("Please pay")
@app.route('/booking/<int:hotelid>/<int:roomid>', methods=['GET', 'POST'])
def booking(hotelid, roomid):
	data = {}
	con.execute("SELECT room_detail.id, room_detail.roomtype, room_detail.roomamenities, room_detail.ratedescription, guests, onsiterate, ratetype, maxoccupancy, ispromo, discount, mealinclusiontype, room_price.hotelid from room_detail inner join room_price on room_detail.id = room_price.id where hotelcode = %s and room_detail.id=%s ;" %(str(hotelid),str(roomid)))
	res = con.fetchone()

	data['username'] = session['username']
	data['room'] = res[2]
	fromD = "10-05-2003"
	toD = "15-05-2003"
	data['from'] = "10-05-2003"
	data['to'] = "15-05-2003"
	a = datetime.strptime(fromD, '%d-%m-%Y').date()
	b = datetime.strptime(toD, '%d-%m-%Y').date()
	
	
	data['discount'] = (res[9]) * ((b-a).days)
	data['rawPay'] = (res[5]) * ((b-a).days)
	data['toPay'] = (res[5]-res[9]) * ((b-a).days)
	
	con.execute("select hotelname from hotel_detail where hotelid=%s;"%(str(hotelid)))
	
	data['error'] = None
	res = con.fetchone()
	print(res)
	data['hotelName'] = res[0]
	
	if request.method == 'POST':
		con.execute("select walletbalance from users where username=%s;"%("'"+data['username']+"'"))
		bal = float(con.fetchone()[0])
		if(bal>data['toPay']):
			bal = bal - data['toPay']
			con.execute("update users set walletbalance=%s where username=%s"%(str(bal),"'"+str(session['username'])+"'"))
			
			con.execute("select * from bookings;")
			nextId = 1
			if(not(len(con.fetchall())==0)):	
				con.execute("select max(bookingid) from bookings;")
				nextId = con.fetchall()[0][0] + 1
			con.execute("select userid from users where username=%s"%("'"+data['username']+"'"))
			userid = con.fetchone()[0]
			
			con.execute("insert into bookings values (%s,%s,%s,%s,%s,%s,%s,%s);",(nextId,userid,roomid,data['toPay'],datetime.now(timezone.utc)
,hotelid,fromD,toD))
	

			return redirect(url_for('user_dashboard'))
			
		else:
			data['error'] = "Bal Not enough. Please add money to your wallet"
		
	return render_template('pay.html',data = data)
	#return "Hotel: " + str(hotelid) + ",\t Roomid: " + str(roomid)
	

	
@app.route('/addMoney', methods=['GET', 'POST'])
def addMoney():
	username = session['username']
	error = None
	if request.method == 'POST':
		print("Yes")
		con.execute("select walletbalance from users where username=%s;"%("'"+session['username']+"'"))
		bal = float(con.fetchone()[0])
		if(float(request.form['amtAdd'])>0):
			bal = bal + float(request.form['amtAdd'])
			con.execute("update users set walletbalance=%s where username=%s"%(str(bal),"'"+str(session['username'])+"'"))
		
#		con.execute("SELECT * FROM users where username = %s and password = %s ;",(request.form['username'],request.form['password']))
#		x = con.fetchall()
#		if len(x)<=0:
#			error = 'Invalid Credentials. Please try again.'
#		else:
#			session['username'] = request.form['username']
			return redirect(url_for('welcome'))
	return render_template('addMoney.html', username = username,error=error)





if __name__ == '__main__':
    app.run(debug=True)

