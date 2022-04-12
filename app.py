from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from dotenv import load_dotenv
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import os

# load_dotenv()

# database_uri = "postgresql:" + ":".join(os.environ.get("DATABASE_URL", "").split(":")[1:])
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "app.sqlite")

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)
bcrypt = Bcrypt(app)

users_table = db.Table('users_table',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.artist_id'))
)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    blogs = db.relationship('Blog', backref='user', cascade='all, delete, delete-orphan')

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Artist(User):
    __tablename__ = 'artist'
    artist_id = db.Column(db.Integer, primary_key=True)
    artist_username = db.Column(db.String, unique=True, nullable=False)
    artist_password = db.Column(db.String, nullable=False)
    motto = db.Column(db.String, nullable=True)
    userFk = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, username, password, motto):
        super().__init__(username, password)
        self.motto = motto

def generate_return_data(schema):
    if isinstance(schema, dict):
        print("DICT")
        user = db.session.query(User).filter(User.id == schema.get("id")).first()
    elif isinstance(schema, list):
        print("LIST")
        user = db.session.query(User).filter(User.id == schema[0].get("id")).first()
    
    return {
        "user": user_schema.dump(user)
    }


@app.route('/user/add', methods=['POST'])
def add_user():
    if request.content_type != 'application/json':
        return jsonify("Error: Data must be JSON.")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    possible_duplicate = db.session.query(User).filter(User.username == username).first()

    if possible_duplicate is not None:
        return jsonify('Error: That username is Taken.')
    
    encrypted_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username, encrypted_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify('New user has been added.')

@app.route('/user/verify', methods=['POST'])
def verify_user():
    if request.content_type != 'application/json':
        return jsonify('Error: Data must be JSON.')

    post_data = request.get_json()
    username = post_data.get('username')
    password = post_data.get('password')

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify('User NOT verified.')

    if bcrypt.check_password_hash(user.password, password) == False:
        return jsonify('User NOT verified')

    return jsonify('User has been verified.')
    

@app.route("/user/get", methods=["GET"])
def get_all_users():
    all_users = db.session.query(User).all()
    return jsonify(multiple_user_schema.dump(all_users))

@app.route('/user/get/<id>', methods=['GET'])
def get_user_by_id(id):
    user = db.session.query(User).filter(User.id == id).first()
    return_data = generate_return_data(user_schema.dump(user))   
    return jsonify(return_data)

@app.route('/user/get/username/<username>', methods=['GET'])
def get_user_by_username(username):
    user = db.session.query(User).filter(User.username == username).first()
    return jsonify(user_schema.dump(user))

@app.route('/user/delete', methods=['DELETE'])
def delete_users():
    all_users = db.session.query(User).all()
    for user in all_users:
        db.session.delete(user)
    db.session.commit()
    return jsonify("All users have has been deleted.")

class Blog(db.Model):
    __tablename__ = 'blog'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=True, unique=True)
    author = db.Column(db.String, nullable=True)
    byline = db.Column(db.String(144), nullable=True)
    body = db.Column(db.String, nullable=True)
    created = db.Column(db.String, nullable=False)
    userFk = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __init__(self, title, author, byline, body, created, userFk):
        self.title = title
        self.author = author
        self.byline = byline
        self.body = body
        self.created = created
        self.userFk = userFk

class BlogSchema(ma.Schema):
    class Meta: 
        fields = ("id", "title", "author", "byline", "body", "created", "userFk")

blog_schema = BlogSchema()
multiple_blog_schema = BlogSchema(many=True)

@app.route("/blog/add", methods=["POST"])
def add_blog():
    if request.content_type != "application/json":
        return jsonify('Error: Data must be JSON.')

    post_data = request.get_json()
    title = post_data.get('title')
    author = post_data.get('author')
    byline = post_data.get('byline')
    body = post_data.get('body')
    created = post_data.get('created')
    userFk = post_data.get('userfk')

    new_record = Blog(title, author, byline, body, created, userFk)
    db.session.add(new_record)
    db.session.commit()

    return_data = generate_return_data(blog_schema.dump(new_record))
    return jsonify(return_data)

@app.route("/blog/get", methods=["GET"])
def get_blogs():
    blogs = db.session.query(Blog).all()
    return_data = generate_return_data(multiple_blog_schema.dump(blogs)) 
    return jsonify(return_data)

@app.route('/blog/get/<id>', methods=['GET'])
def get_blog_by_id(id):
    blog = db.session.query(Blog).filter(Blog.id == id).first()
    return jsonify(blog_schema.dump(blog))

@app.route('/blog/delete/<id>', methods=['DELETE'])
def delete_blog_by_id(id):
    blog = db.session.query(Blog).filter(Blog.id == id).first()
    db.session.delete(blog)
    db.session.commit()
    return jsonify("Blog has been deleted.")

@app.route('/blog/update/<id>', methods=['PUT'])
def update_blog_by_id(id):
    if request.content_type != "application/json":
        return jsonify("Error: Data must be json")

    post_data = request.get_json()
    title = post_data.get('title')
    author = post_data.get('author')
    byline = post_data.get('byline')
    body = post_data.get('body')

    blog = db.session.query(Blog).filter(Blog.id == id).first()

    blog.title = title
    blog.author = author
    blog.byline = byline
    blog.body = body

    db.session.commit()
    return jsonify("Blog Updated Successfully")

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'blogs')
    blogs = ma.Nested(multiple_blog_schema)
user_schema = UserSchema()
multiple_user_schema = UserSchema(many=True)

class ArtistSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username', 'motto', 'blogs')
    blogs = ma.Nested(multiple_blog_schema)

artist_schema = ArtistSchema()
multiple_artist_schema = ArtistSchema(many=True)

if __name__ == "__main__":
    app.run(debug=True)