import jwt
from time import time
from app import db, login_manager
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

association_table = db.Table(
    'association_table',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    followed = db.relationship(
        'User',
        secondary=association_table,
        primaryjoin=(association_table.c.follower_id == id),
        secondaryjoin=(association_table.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        # https://gravatar.loli.net/avatar
        return 'https://gravatar.loli.net/avatar/{}?d=identicon&s={}'.format(digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        count = self.followed.filter(association_table.c.followed_id == user.id).count()
        return count > 0

    def get_followed_posts(self):
        followed_posts = Post.query \
            .join(association_table, (association_table.c.followed_id == Post.user_id)) \
            .filter(association_table.c.follower_id == self.id)
        own_posts = Post.query.filter_by(user_id=self.id)
        return followed_posts.union(own_posts).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        token = jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=['HS256']
            )['reset_password']
        except:
            return

        return User.query.get(id)

    def __repr__(self):
        return '<User: {}>'.format(self.username)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post: {}...>'.format(self.body[:20])


# Because Flask-Login knows nothing about databases, it needs the application's help in loading a user.
# For that reason, the extension expects that the application will configure a user loader function,
# that can be called to load a user given the ID.
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
