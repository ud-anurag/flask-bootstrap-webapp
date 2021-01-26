from flask import Flask,render_template, request, session, redirect
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
    content = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    date = db.Column(db.String(20), nullable = False)
    sub_title = db.Column(db.String(120), nullable=False)
    img_name = db.Column(db.String(12), nullable=False)

@app.route('/')
def index():
    posts = Posts.query.filter_by().all()[0:params['no_of_posts']]
    post=Posts.query.filter_by().first()
    return render_template("index.html", params = params, blog = blog, posts=posts,post=post)

@app.route('/about')
def about():
    post=Posts.query.filter_by().first()
    return render_template("about.html", params = params, blog = blog,post=post)

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
    post=Posts.query.filter_by().first()
    return render_template("contact.html", params=params, blog=blog,post=post)


@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    
    return render_template("post.html", params=params, blog=blog, post=post)


@app.route('/dashboard', methods = ['GET','POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        post=Posts.query.filter_by().first()
        return render_template("dashboard.html", params=params, blog=blog, posts=posts,post=post)
    if (request.method == 'POST'):
        username = request.form.get('name')
        password = request.form.get('password')
        if (username==params['admin_username'] and password==params['admin_pwd']):
            session['user'] = username
            posts = Posts.query.all()
            post=Posts.query.filter_by().first()
            return render_template("dashboard.html", params=params, blog=blog, posts=posts,post=post)
        else:
            return render_template("login.html", params=params)

    else:
        return render_template("login.html", params=params)

@app.route("/edits/<string:sno>", methods = ['GET','POST'])
def edits(sno):
    if('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            title = request.form.get('title')
            sub_title = request.form.get('subtitle')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_name=request.form.get('img_name')
            if (sno == '0'):
                post = Posts(title=title, sub_title=sub_title, content=content, slug=slug,img_name=img_name,date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.sub_title = sub_title
                post.content = content
                post.slug = slug
                post.img_name = img_name
                post.date=datetime.now()
                db.session.commit()
                return redirect("/edits/"+sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template("edits.html",params=params,post=post,blog=blog)

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/")

app.run(debug=True)