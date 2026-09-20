from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "gracebook.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "change-this-secret-key"

db = SQLAlchemy(app)

# Every post belongs to one of these sections. Adding a new section later
# (Bible Studies, Events, etc.) just means adding one more entry here.
SECTIONS = {
    "feed": {
        "label": "Feed",
        "template": "feed.html",
        "prompt": "Share a testimony, encouragement, or update...",
        "verse": None,
    },
    "prayer": {
        "label": "Prayer Wall",
        "template": "prayer_wall.html",
        "prompt": "Share a prayer request...",
        "verse": "\"For where two or three gather in my name, there am I with them.\" — Matthew 18:20",
    },
    "testimony": {
        "label": "Testimonies",
        "template": "testimonies.html",
        "prompt": "Share how Jesus has worked in your life...",
        "verse": "\"They triumphed over him by the blood of the Lamb and by the word of their testimony.\" — Revelation 12:11",
    },
    "discussion": {
        "label": "Discussion",
        "template": "discussion.html",
        "prompt": "Start a discussion or ask a question...",
        "verse": "\"As iron sharpens iron, so one person sharpens another.\" — Proverbs 27:17",
    },
}


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    bio = db.Column(db.String(300), nullable=True)
    posts = db.relationship("Post", backref="author", lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    section = db.Column(db.String(20), nullable=False, default="feed")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comments = db.relationship(
        "Comment", backref="post", lazy=True, order_by="Comment.created_at"
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


def get_or_create_demo_user():
    """Temporary helper until real sign-in is built."""
    user = User.query.first()
    if not user:
        user = User(name="Friend", bio="New to Gracebook")
        db.session.add(user)
        db.session.commit()
    return user


def render_section(section_key):
    section = SECTIONS[section_key]
    posts = (
        Post.query.filter_by(section=section_key)
        .order_by(Post.created_at.desc())
        .all()
    )
    return render_template(
        section["template"],
        posts=posts,
        section_key=section_key,
        section_label=section["label"],
        verse=section["verse"],
    )


@app.route("/")
def feed():
    return render_section("feed")


@app.route("/prayer-wall")
def prayer_wall():
    return render_section("prayer")


@app.route("/testimonies")
def testimonies():
    return render_section("testimony")


@app.route("/discussion")
def discussion():
    return render_section("discussion")


def _route_name_for_section(section_key):
    return {
        "feed": "feed",
        "prayer": "prayer_wall",
        "testimony": "testimonies",
        "discussion": "discussion",
    }[section_key]


@app.route("/post/new", methods=["GET", "POST"])
def new_post():
    if request.method == "POST":
        user = get_or_create_demo_user()
        content = request.form.get("content", "").strip()
        section_key = request.form.get("section", "feed")
        if section_key not in SECTIONS:
            abort(400)
        if content:
            post = Post(content=content, section=section_key, user_id=user.id)
            db.session.add(post)
            db.session.commit()
        return redirect(url_for(_route_name_for_section(section_key)))
    return render_template("new_post.html", sections=SECTIONS)


@app.route("/post/<int:post_id>/comment", methods=["POST"])
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    user = get_or_create_demo_user()
    content = request.form.get("content", "").strip()
    if content:
        comment = Comment(content=content, post_id=post_id, user_id=user.id)
        db.session.add(comment)
        db.session.commit()
    return redirect(url_for(_route_name_for_section(post.section)))


@app.route("/profile")
def profile():
    user = get_or_create_demo_user()
    return render_template("profile.html", user=user)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
