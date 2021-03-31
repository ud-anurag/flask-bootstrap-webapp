import sentry_sdk
from sentry_sdk.integrations.flask import \
    FlaskIntegration
from flask import Flask, render_template, request, session, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_mail import Mail
import json
import math
import pandas as pd
import numpy as np


with open("config.json", "r") as c:
    json = json.load(c)

params = json['params']

sentry_sdk.init(
    dsn="https://38a6fe473edf47efbb4b06381cb94d2a@o518556.ingest.sentry.io/5627698",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

app = Flask(__name__)
app.secret_key = 'super secret key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail_user'],
    MAIL_PASSWORD=params['gmail_pwd']
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
    date = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    sub_title = db.Column(db.String(120), nullable=False)
    img_name = db.Column(db.String(12), nullable=False)


@app.route('/')
def index():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)
                  * int(params['no_of_posts'])+int(params['no_of_posts'])]
    if (page == 1):
        prev = '/#'
        next = '/?page='+str(page + 1)
    elif (page == last):
        prev = '/?page='+str(page - 1)
        next = '/#'
    else:
        prev = '/?page='+str(page - 1)
        next = '/?page='+str(page + 1)

    return render_template("index.html", params=params, blog=blog, posts=posts, prev=prev, next=next)


@app.route('/about')
def about():
    return render_template("about.html", params=params, blog=blog)


@app.route('/contact', methods=['GET', 'POST'])
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
                          recipients=[params['gmail_user']],
                          body=message + '\n' + phone +
                          '\n' + str(datetime.now())
                          )
    return render_template("contact.html", params=params, blog=blog)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    return render_template("post.html", params=params, blog=blog, post=post)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user'] == params['admin_username']):
        posts = Posts.query.all()
        post = Posts.query.filter_by().first()
        return render_template("dashboard.html", params=params, blog=blog, posts=posts, post=post)
    if (request.method == 'POST'):
        username = request.form.get('name')
        password = request.form.get('password')
        if (username == params['admin_username'] and password == params['admin_pwd']):
            session['user'] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, blog=blog, posts=posts)
        else:
            return render_template("login.html", params=params)

    else:
        return render_template("login.html", params=params)


@app.route("/edits/<string:sno>", methods=['GET', 'POST'])
def edits(sno):
    if('user' in session and session['user'] == params['admin_username']):
        if (request.method == 'POST'):
            title = request.form.get('title')
            sub_title = request.form.get('subtitle')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_name = request.form.get('img_name')
            if (sno == '0'):
                post = Posts(title=title, sub_title=sub_title, content=content,
                             slug=slug, img_name=img_name, date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Posts.query.filter_by(sno=sno).first()
                post.title = title
                post.sub_title = sub_title
                post.content = content
                post.slug = slug
                post.img_name = img_name
                post.date = datetime.now()
                db.session.commit()
                return redirect("/edits/"+sno)
    post = Posts.query.filter_by(sno=sno).first()
    return render_template("edits.html", params=params, post=post, blog=blog)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/")


@app.route("/covid")
def covid():
    dataset = pd.read_csv(
        "D:\Flask\\flask-bootstrap-webapp\static\cases\\covid_19_data.csv")
    dataset['ObservationDate'] = pd.to_datetime(dataset['ObservationDate'])
    dataset = dataset.loc[dataset["Country"] == "India"].head(100)
    dataset = dataset.sort_values(by=['Confirmed'], ascending=False)
    del dataset["Province/State"]
    dataset.set_index("ObservationDate", inplace=True)

    return render_template("covid.html", blog=blog, params=params, tables=dataset.to_html(classes="table table-hover"))


# @app.route(/visualize)
# def visualize():
#     dataset = pd.read_csv(
#         "D:\Flask\\flask-bootstrap-webapp\static\cases\\covid_19_data.csv")
#     print(dataset.head())
#     dataset.dropna(axis='columns', inplace=True)
#     dataset_new = dataset.groupby(["Country"])
#     for name, group in dataset_new:
#         sum1 = group["Confirmed"].sum()
#         print(f"{name}:{sum1}")


@app.route("/delete/<string:sno>", methods=['GET', 'POST'])
def delete(sno):
    if('user' in session and session['user'] == params['admin_username']):
        post = Posts.query.filter_by(sno=sno).first()
        print(post)
        db.session.delete(post)
        db.session.commit()
        posts = Posts.query.all()
    return redirect("/dashboard")


app.run(debug=True)
