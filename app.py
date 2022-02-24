import psycopg2
from flask import Flask, render_template, redirect, url_for, request


def connect():
    conn = psycopg2.connect(
    host="localhost",
    database="dbmsproject",
    user="postgres",
    password = "km123"
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
    			con.execute("select max(userid) from users;")
    			nextId = con.fetchall()[0][0] + 1
    			con.execute("insert into users values (%s,%s,%s,%s,%s,%s,%s,0);",(nextId,request.form['username'],request.form['password'],request.form['name'],request.form['address'],request.form['email'],request.form['phone']))

    			return redirect(url_for('welcome'))
    	return render_template('register.html', error=error)


if __name__ == '__main__':
    app.run(debug=True)

