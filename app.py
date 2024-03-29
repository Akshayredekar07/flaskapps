from flask import Flask, render_template, url_for, request, session , redirect
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import os
import math


with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server = True
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['user_gmail'],
    MAIL_PASSWORD = params['user_passward'],


)

mail = Mail(app)


if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']

db = SQLAlchemy(app)


class Contacts(db.Model):
    serial_no=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(80),   nullable=False)
    email=db.Column(db.String(50),      nullable=False)
    phoneNumber=db.Column(db.String(12),    nullable=False)
    message=db.Column(db.String(120),   nullable=False)
    date=db.Column(db.String(20),   nullable=True)

class Posts(db.Model):
    serial_no=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(80),   nullable=False)
    tagline=db.Column(db.String(80),   nullable=False)
    content=db.Column(db.String(50),      nullable=False)
    date=db.Column(db.String(20),   nullable=True)
    slug=db.Column(db.String(45),   nullable=False)
    img_file=db.Column(db.String(20),   nullable=True)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    if page==1:
        prev = "#"
        next = "/?page="+ str(page+1)
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    else:
        prev = "/?page="+ str(page-1)
        next = "/?page="+ str(page+1)
    
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)



@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():

    if('user' in session and session['user'] == params['admin_user']):
        posts = Posts.query.all()
        return render_template('dashboard.html', params=params, posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_passward']):
            #SET THE SESSION VARIABLE
            session['user'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=posts)
    return render_template('login.html', params=params)


@app.route("/edit/<string:serial_no>", methods=['GET', 'POST'])
def edit(serial_no):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if serial_no == '0':
                post=Posts(title=box_title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
        
            else:
                post = Posts.query.filter_by(serial_no=serial_no).first()
                post.box_title = box_title
                post.tline = tline
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.commit()
                return redirect('/edit/'+serial_no)

    post = Posts.query.filter_by(serial_no=serial_no).first()
    return render_template('edit.html', params=params, post=post, serial_no=serial_no)




@app.route("/about")
def about():
    bgImg = url_for('static', filename='assets/img/about-bg.jpg')
    return render_template('about.html', background_image_url=bgImg, params=params)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')
   
@app.route("/delete/<string:serial_no>", methods=['GET', 'POST'])
def delete(serial_no):
    if('user' in session and session['user'] == params['admin_user']):
        post = Posts.query.filter_by(serial_no=serial_no).first()
        # Check if the post exists
        if post:
            db.session.delete(post)
            db.session.commit()
    return redirect('/dashboard')  



@app.route("/uploader", methods=['GET', 'POST'])
def uploader():
    if('user' in session and session['user'] == params['admin_user']):
        if(request.method =='POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Upload succesful!"



@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if(request.method =='POST'):
        # print("Form submitted!")
        '''Add Entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, phoneNumber=phone, message=message, email=email, date=datetime.now())
        db.session.add(entry)
        db.session.commit()

        #Send email to multiple recipients
        recipients = [params['user_gmail']]
        mail.send_message('New Message from Blog - ' + name,
                          sender=email, 
                          recipients=recipients,
                          body=message + "\n" + phone
                         )
        
    bgImg = url_for('static', filename='assets/img/contact-bg.jpg')
    return render_template('contact.html', background_image_url=bgImg, params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):
    post = Posts.query.filter_by(slug=post_slug).first()
    bgImg = url_for('static', filename='assets/img/' + post.img_file)
    return render_template('post.html', background_image_url=bgImg, params=params, post=post)

app.secret_key = 'super-secret-key'

if __name__ == "__main__":
    app.run(debug=True)
