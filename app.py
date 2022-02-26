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


@app.route('/register', methods=['GET', 'POST'])
def register():	
    	error = None
    	if request.method == 'POST':
    		usern = request.form['username'];
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
   
   
@app.route('/show', methods=['GET', 'POST'])
def show():	
    
	error = 0
	data = {}

	con.execute("SELECT DISTINCT country from hotel_detail order by country ;")
	data['country'] = con.fetchall()

	if len(data['country'])<=0:
		error = 1

	if request.method == 'POST':
		op1 = request.form.get('option1')
		op2 = request.form.get('option2')    		
    		

		if op1 and op2:
			con.execute("SELECT hotelname, address, city, country FROM hotel_detail where country = '%s' and city = '%s' LIMIT 10 ;"%(request.form['country'],request.form['city']))
    		
		elif op1:
			con.execute("SELECT hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country']))	
			print(request.form.get('country'))
			print(con.mogrify("SELECT hotelname, address, city, country FROM hotel_detail where country = '%s' LIMIT 10 ;"%(request.form['country'])))
		else:
			con.execute("SELECT hotelname, address, city, country FROM hotel_detail where city = '%s' LIMIT 10 ;"%request.form['city'])
    		
		data['data'] = con.fetchall()
		if len(data['data'])<=0:
			error = 1
    	
	data['error'] = error
    	
	print(data)
	return render_template('show_hotels.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)

