from flask import Flask,render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json

with open("config.json","r") as c:
    json = json.load(c)

params = json['params']
app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 465,
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail_user'],
    MAIL_PASSWORD = params['gmail_pwd']
)
mail = Mail(app)
if(params['local_server']):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

blog = json['blog']

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone_num = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable = False)

class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    date = db.Column(db.String(20), nullable = False)
    sub_title = db.Column(db.String(120), nullable=False)
    img_name = db.Column(db.String(12), nullable=False)

@app.route('/')
def index():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    return render_template("index.html", params = params, blog = blog, posts=posts)

@app.route('/about')
def about():
    return render_template("about.html", params = params, blog = blog)

@app.route('/contact', methods = ['GET','POST'])
def contact():
    if (request.method == 'POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, phone_num=phone, msg=message)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New mail from User: '+name,
             sender=email,
             recipients = [params['gmail_user']],
             body = message +'\n' + phone + '\n' + str(datetime.now())
            )
    return render_template("contact.html", params=params, blog=blog)


@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    
    return render_template("post.html", params=params, blog=blog, post=post)


@app.route('/dashboard', methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, blog=blog, posts=posts)
    if (request.method == 'POST'):
        username = request.form.get('name')
        password = request.form.get('password')
        if (username==params['admin_username'] and password==params['admin_pwd']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, blog=blog, posts=posts)
        else:
            return render_template("login.html", params=params)

    else:
        return render_template("login.html", params=params)

app.run(debug=True)
