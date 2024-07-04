import os
import ssl
import random

from sqlalchemy import text

from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
#from flask_uploads import configure_uploads, UploadSet, IMAGES

ssl._create_default_https_context = ssl._create_unverified_context
TEMPLATES_AUTO_RELOAD = True



GM_API =os.environ.get("DRUM_API")

app = Flask(__name__)
app.secret_key = "zacuscacuvinetesiciuperciafumate"
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///concierge.db'
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads'
app.config['SESSION_COOKIE_MAX_SIZE'] = 'size_in_bytes'

#app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)
#db.init_app(app)

#photos = UploadSet('photos', IMAGES)
#configure_uploads(app, photos)

class User(db.Model):

    #Relationships created with the users class
    #u sers: one to many their wishes
    # users: one to many with their relationships
    # user: one to many wth their friends
    # user: one to many with occasions
    # user: many to many with the groups they're a part of
    # user: many to many with the gifts they offer (if individual, they should be one to many, but as part of groups, they become many to many
    # user: many to many with questions

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column("username", db.String(20), nullable=False)
    password = db.Column("password", db.String(35))
    email = db.Column("email", db.String(70), unique=True)


    friendships_initiated = db.relationship("Friendships", foreign_keys="[Friendships.friend_initiating_id]",
                                            back_populates="initiating_user")
    friendships_accepted = db.relationship("Friendships", foreign_keys="[Friendships.friend_accepting_id]",
                                           back_populates="accepting_user")

    wishes = db.relationship('Wish', back_populates='user')
    relationships = db.relationship('Relationship', back_populates='user')
    gifts = db.relationship('Gift', secondary='users_gifts', back_populates='user')
    groups = db.relationship('Group', secondary='users_groups', back_populates='user')
    questions = db.relationship('Question', secondary='users_questions', back_populates='user')
    occasions = db.relationship('Occasion', back_populates='user')
    likes = db.relationship('Like', back_populates='user')
    comments = db.relationship('Comment', back_populates='user')




    users_groups = db.Table('users_groups',
                            db.Column('users_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                            db.Column('groups_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True))

    users_gifts = db.Table('users_gifts',
                            db.Column('users_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                            db.Column('gifts_id', db.Integer, db.ForeignKey('gifts.id'), primary_key=True))

    users_questions = db.Table('users_questions',
                            db.Column('users_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                            db.Column('questions_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True))

    seating_preferences = db.Table('seating_preferences', db.Model.metadata,
                                   db.Column('user_id', db.Integer, db.ForeignKey('users.id')),
                                   db.Column('group_id', db.Integer, db.ForeignKey('groups.id'))
                                   )

    seating_preferences = db.relationship('User', secondary='seating_preferences',
                                          primaryjoin=id == seating_preferences.c.user_id,
                                          secondaryjoin=id == seating_preferences.c.group_id,
                                          backref='preferred_by_users')

    def __repr__(self):
        wishes_str = ', '.join(wishes.name for wishes in self.wishes)
        relationships_str = ', '.join(relationships.name for relationships in self.relationships)
        groups_str = ', '.join(groups.name for groups in self.groups)
        return f"User(id={self.id}, username='{self.username}', wishes=[{wishes_str}],relationships=[{relationships_str}], groups=[{groups_str}])"

    def create_wishlists(self, wishes):
        return wishes.wishlist in self.wishlist

    def create_occasion(self, occasions):
        return occasions.name in self.occasions

class Wish (db.Model):

    #relationships:
    # one to many with users
    # many to many with occasions
    # many to many with groups
    # many to many with gifts
    # one to many with likes
    # one to many with comments

    __tablename__ = "wishes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    image = db.Column('image', db.String)
    wishlist = db.Column("wishlist", db.String(100))
    link = db.Column("link", db.String(200))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='wishes')
    groups = db.relationship('Group', secondary='wishes_groups', back_populates='wishes')
    gifts = db.relationship('Gift', secondary='wishes_gifts', back_populates='wishes')
    occasions_id = db.Column(db.Integer, db.ForeignKey('occasions.id'))
    occasions = db.relationship('Occasion', back_populates='wishes')
    likes_id = db.Column(db.Integer, db.ForeignKey('likes.id'))
    likes = db.relationship('Like', back_populates='wish')
    comments = db.relationship('Comment', back_populates='wish')  # Added this line

    wishes_groups = db.Table('wishes_groups',
                             db.Column('wishes_id', db.Integer, db.ForeignKey('wishes.id'), primary_key=True),
                             db.Column('groups_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True))

    wishes_gifts = db.Table('wishes_gifts',
                            db.Column('wishes_id', db.Integer, db.ForeignKey('wishes.id'), primary_key=True),
                            db.Column('gifts_id', db.Integer, db.ForeignKey('gifts.id'), primary_key=True))

    wishes_occasions = db.Table('wishes_occasions',
                                db.Column('wishes_id', db.Integer, db.ForeignKey('wishes.id'), primary_key=True),
                                db.Column('occasions_id', db.Integer, db.ForeignKey('occasions.id'), primary_key=True))

    def __repr__(self):
        groups_str = ', '.join(groups.name for groups in self.groups)
        gifts_str = ', '.join(gifts.name for gifts in self.gifts)
        occasions_str = ', '.join(gifts.name for gifts in self.occasion)
        return f"Wish(id={self.id}, name='{self.name}', occasions=[{occasions_str}], groups=[{groups_str}], gifts=[{gifts_str}])"


class Relationship(db.Model):
    __tablename__ = "relationships"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    liaison = db.Column(db.String)
    cultural_identity = db.Column(db.String)
    religious_restrictions = db.Column(db.String)
    allergies = db.Column(db.String)
    sexual_orientation = db.Column(db.String)
    dietary_preferences = db.Column(db.String)
    answer = db.Column(db.String(500))

    user = db.relationship('User', back_populates='relationships')
    occasions = db.relationship('Occasion', back_populates='relationships')
    questions = db.relationship('Question', secondary='relationships_questions', back_populates='relationships')
    groups = db.relationship('Group', back_populates='relationships')
    gifts = db.relationship('Gift', secondary='relationships_gifts', back_populates='relationships')
    involvementlevels = db.relationship('Involvement', secondary='relationships_involvementlevels', back_populates='relationships')

    relationships_questions = db.Table('relationships_questions',
                            db.Column('relationships_id', db.Integer, db.ForeignKey('relationships.id'), primary_key=True),
                            db.Column('questions_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True))

    relationships_gifts = db.Table('relationships_gifts',
                                   db.Column('relationships_id', db.Integer, db.ForeignKey('relationships.id'),
                                             primary_key=True),
                                   db.Column('gifts_id', db.Integer, db.ForeignKey('gifts.id'), primary_key=True))

    relationships_involvementlevels = db.Table('relationships_involvementlevels',
                                   db.Column('relationships_id', db.Integer, db.ForeignKey('relationships.id'),
                                             primary_key=True),
                                   db.Column('involvementlevels_id', db.Integer, db.ForeignKey('involvementlevels.id'), primary_key=True))

    def __repr__(self):
        involvementlevels_str = ', '.join(involvementlevels.involvement for involvementlevels in self.involvementlevels)
        return f"Relationship(id={self.id}, name='{self.name}', liaison='{self.liaison}', involvement=[{involvementlevels_str}])"


class Question (db.Model):

    #relationships:
    # questions: many to many with the levels of involvment
    # questions: many to many with users
    # questions: many to many with occasions

    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column("question", db.String(500), nullable=False)

    involvementlevels = db.relationship('Involvement', secondary='questions_involvementlevels', back_populates='questions')
    occasions = db.relationship('Occasion', secondary='questions_occasions', back_populates='questions')
    relationships = db.relationship('Relationship', secondary='relationships_questions', back_populates='questions')
    user = db.relationship('User', secondary='users_questions', back_populates='questions')

    questions_involvementlevels = db.Table('questions_involvementlevels',
                                   db.Column('questions_id', db.Integer, db.ForeignKey('questions.id'),
                                             primary_key=True),
                                   db.Column('involvementlevels_id', db.Integer, db.ForeignKey('involvementlevels.id'), primary_key=True))

    questions_occasions = db.Table('questions_occasions',
                                           db.Column('questions_id', db.Integer, db.ForeignKey('questions.id'),
                                                     primary_key=True),
                                           db.Column('occasions_id', db.Integer,
                                                     db.ForeignKey('occasions.id'), primary_key=True))

    selected_questions = db.Table('selected_questions', db.Model.metadata,
                               db.Column('relationship_id', db.Integer, db.ForeignKey('relationships.id'), primary_key=True),
                               db.Column('question_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True))

    selected_questions = db.relationship('Question', secondary=selected_questions, backref='selected_in_relationships')

    def __repr__(self):
        involvementlevels_str = ', '.join(involvementlevels.involvement for involvementlevels in self.involvement)
        return f"Question(id={self.id}, question='{self.question}', involvement=[{involvementlevels_str}])"

class Involvement(db.Model):

    #relationships:
    # many to many with questions
    # many to many with relationships

    __tablename__ = "involvementlevels"
    id = db.Column(db.Integer, primary_key=True)
    involvment = db.Column("involvment", db.String(100), nullable=False)

    questions = db.relationship('Question', secondary='questions_involvementlevels', back_populates='involvementlevels')
    relationships = db.relationship('Relationship', secondary='relationships_involvementlevels', back_populates='involvementlevels')
    occasions_id = db.Column(db.Integer, db.ForeignKey('occasions.id'))
    occasions = db.relationship('Occasion', back_populates='involvementlevels')

    def __repr__(self):
        questions_str = ', '.join(questions.questions for questions in self.question)
        return f"Involvement(id={self.id}, question=[{questions_str}])"

class Gift (db.Model):

    # gifts: many to many with wishes (the same wish; eg: red roses can be interpreted through various gifts)
    # gifts: many to many with users (you don't offer the same thing each year for the same occasion)
    # many to one with groups (one group can five many gifts, but the same gift can only be given by no more than one group)
    # many to many with relationships (if individual, the relationship would be one to many, but if a group buys a
    # gift for the same common friend then it becomes many to many)
    # one to one with occasions

    __tablename__ = "gifts"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    image = db.Column('image', db.String)
    answer = db.Column("answer", db.String(100))
    budget = db.Column("budget",db.Integer)

    user = db.relationship('User', secondary='users_gifts', back_populates='gifts')
    groups = db.relationship('Group', secondary='gifts_groups', back_populates='gifts')
    wishes = db.relationship('Wish', secondary='wishes_gifts', back_populates='gifts')
    relationships = db.relationship('Relationship', secondary='relationships_gifts', back_populates='gifts')
    occasions_id = db.Column(db.Integer, db.ForeignKey('occasions.id'))
    occasions = db.relationship('Occasion', back_populates='gifts')


    gifts_groups = db.Table('gifts_groups',
                                           db.Column('gifts_id', db.Integer, db.ForeignKey('gifts.id'),
                                                     primary_key=True),
                                           db.Column('groups_id', db.Integer,
                                                     db.ForeignKey('groups.id'), primary_key=True))

    def __repr__(self):
        wishes_str = ', '.join(wishes.name for wishes in self.wishes)
        users_str = ', '.join(users.username for users in self.users)
        groups_str = ', '.join(groups.name for groups in self.groups)
        return f"Gift(id={self.id}, wishes=[{wishes_str}], users=[{users_str}], groups=[{groups_str}])"

    def has_allergens(self, relationships):
        return relationships.allergies in self.relationships

    def has_cultural_identity(self, relationships):
        return relationships.cultural_identity in self.relationships

    def has_cultural_identity(self, relationships):
        return relationships.religious_restrictions in self.relationships



class Group(db.Model):

    # groups: many to many with users
    # groups: many to many with wishes
    # groups: many to many with gifts (to not repeat gifts from one year to another)
    # one to many with relationships (the same relation can be celebrated across many groups)
    # many to one with occasions (the same group can be formed for distinctive occasions,

    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column("name", db.String(100), nullable=False)
    image = db.Column('image', db.String)
    attendance = db.Column('attendance', db.Boolean)
    date_time = db.Column(db.DateTime)
    religious_restrictions = db.Column('religious_restrictions', db.Boolean)
    allergies = db.Column('allergies', db.Boolean)
    dietary_preferences = db.Column('dietary_preferences', db.String)

    relationships_id = db.Column(db.Integer, db.ForeignKey("relationships.id"))
    relationships = db.relationship('Relationship', back_populates='groups')
    user = db.relationship('User', secondary='users_groups', back_populates='groups')
    gifts = db.relationship('Gift', secondary='gifts_groups', back_populates='groups')
    wishes = db.relationship('Wish', secondary='wishes_groups', back_populates='groups')
    occasions = db.relationship('Occasion', back_populates='groups')
    occasions_id = db.Column(db.Integer, db.ForeignKey('occasions.id'))
    comments = db.relationship('Comment', back_populates='groups')
    comments_id = db.Column(db.Integer, db.ForeignKey('comments.id'))



    def __repr__(self):
        relationships_str = ', '.join(relationships.liaison for relationships in self.liaison)
        return f"Group(id={self.id}, name={self.name}, relationships=[{relationships_str}])"


class Occasion(db.Model):

    # occasions are individualised and not approached in a generic undrstanding ( eg : Christmas 2024, not Christmas) which leads to:
    # one to many with user
    # one to many with gifts (the same occasion attracts many gifts)
    # one to many with levels of involvement (eg: dynamics within human interactions can evolve in dfferent direcions across years)
    # one to many with groups (each group is formed around one individual and not genericoccasion)
    # one to many with relationships
    # many to many with wishes (the same wish can prevail across many occasions, such as the same occasion can attract many wishes)
    # many to many wish questions

    __tablename__ = "occasions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    relationships_id = db.Column(db.Integer, db.ForeignKey("relationships.id"))
    name = db.Column("name", db.String(100), nullable=False)
    user = db.relationship('User', back_populates='occasions')
    gifts = db.relationship('Gift', back_populates='occasions')
    involvementlevels = db.relationship('Involvement', back_populates='occasions')
    relationships = db.relationship('Relationship', back_populates='occasions')
    groups = db.relationship('Group', back_populates='occasions')
    wishes = db.relationship('Wish', secondary='wishes_occasions', back_populates='occasions')
    questions = db.relationship('Question', secondary='questions_occasions', back_populates='occasions')

    def __repr__(self):
        return f"Occasion(id={self.id}, name={self.name})"

class Friendships(db.Model):
    __tablename__ = "friendships"
    friendship_id = db.Column(db.Integer, primary_key=True)
    friend_initiating_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    friend_accepting_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    common_relationships = db.Column(db.Integer, db.ForeignKey('relationships.id'))
    initiating_user = db.relationship("User", back_populates="friendships_initiated",
                                      foreign_keys=[friend_initiating_id])
    accepting_user = db.relationship("User", back_populates="friendships_accepted", foreign_keys=[friend_accepting_id])



def __repr__(self):
    return f"({self.friend_initiating}, {self.friend_accepting})"



class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_liking = db.Column(db.Integer, db.ForeignKey('users.id'))

    user = db.relationship('User', back_populates='likes')
    wish = db.relationship('Wish', back_populates='likes')

    def __repr__(self):
        return f"Like(id={self.like_id}, user_liking={self.user_liking}, wish_liked={self.wish_liked})"


    # comments

class Comment(db.Model):

    # one to many with users
    # one to many with wishes
    # one to many with groups

    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(2000))
    date_time = db.Column(db.DateTime)

    user = db.relationship('User', back_populates='comments')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    wish = db.relationship('Wish', back_populates='comments')
    wish_id = db.Column(db.Integer, db.ForeignKey('wishes.id'))
    groups = db.relationship('Group', back_populates='comments')

    def __repr__(self):
        return f"Comment(id={self.comment_id}, user_commenting={self.user_commenting}, wish_commented={self.wish_commented},group_commmented_in={self.group_commmented_in})"




class Messages(db.Model):
    __tablename__ = "messages"
    message_id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.String(2000))
    date_time = db.Column(db.DateTime)

    def __repr__(self):
        return f"({self.sender}, {self.receiver_id}, {self.date_time})"





from sqlalchemy import inspect

with app.app_context():
    db.create_all()

#    inspector = inspect(db.engine)
#    columns = inspector.get_columns('wishes')
#    user_id_exists = any(column['name'] == 'involvementlevels' for column in columns)

#    if not user_id_exists:
#        db.session.execute(text("ALTER TABLE relationships ADD COLUMN involvementlevels STRING;"))
#        db.session.commit()



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user.password == password:
            session["user_id"] = user.id
            return render_template("dashboard.html", user=user)
        else:
            flash("Incorrect username or password.")
            return render_template("login.html")

    return render_template("login.html")


@app.route('/user')
def logged_in_user():
    user_id = None
    if "user_id" in session:
        user_id = session["user_id"]
        return f"<h1> Hi User ID: {user_id}</h1>"
    else:
        flash("Please log in before using the app.")
        return redirect(url_for("login"))


@app.route('/registeraccount', methods=['GET', 'POST'])
def registeraccount():
    if request.method == "POST":
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            password=request.form.get('password')
        )


        db.session.add(new_user)
        db.session.commit()

        session["user_id"] = new_user.id

        return render_template("dashboard.html", user=new_user)
    return render_template("registeraccount.html")

# request gift recommendations
# shuffle questions - in JavaScript
# Confirm question - save answer - table with metadata between questions nd relationships
# trigger search via api
# save search title as answer
# copy wish in wishlist
# add members into groups


@app.route('/newgift', methods=['GET', 'POST'])
def request_gift_rec():
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if user and request.method == "POST":
        name = request.form.get('name')
        involvementlevels = request.form.getlist('involvement')  # Use getlist for multi-select fields
        liaison = request.form.get('type')
        sexual_orientation = request.form.get('sexual_orientation')
        allergies = request.form.get('allergies')
        cultural_identity = request.form.get('cultural_identity')
        religious_restrictions = request.form.get('religious_restrictions')
        dietary_preferences = request.form.get('dietary_preferences')

        print("DEBUG - Form Data:")
        print("Name:", name, type(name))
        print("Involvement Levels:", involvementlevels, type(involvementlevels))
        print("Liaison:", liaison, type(liaison))
        print("Sexual Orientation:", sexual_orientation, type(sexual_orientation))
        print("Allergies:", allergies, type(allergies))
        print("Cultural Identity:", cultural_identity, type(cultural_identity))
        print("Religious Restrictions:", religious_restrictions, type(religious_restrictions))
        print("Dietary Preferences:", dietary_preferences, type(dietary_preferences))

        try:
            new_relationship = Relationship(
                name=name,
                liaison=liaison,
                cultural_identity=cultural_identity,
                religious_restrictions=religious_restrictions,
                allergies=allergies,
                sexual_orientation=sexual_orientation,
                dietary_preferences=dietary_preferences,
                involvementlevels=involvementlevels  # Make sure involvementlevels is a list
            )
            print("DEBUG - New Relationship Object:")
            print(new_relationship)

            db.session.add(new_relationship)
            db.session.commit()

            new_occasion = request.form.get("occasion")
            questions = Question.query.filter_by(liaison=liaison, occasion=new_occasion).all()

            return render_template("recommendations.html", user=user, relationships=new_relationship,
                                   questions=questions)

        except Exception as e:
            print("An error occurred while creating the new_relationship object:", e)

    return render_template("recommendations.html", user=user)




@app.route('/updaterelationship', methods=['GET', 'POST'])
def relationships_management(self, relatioships):
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if user:
        if request.method == "POST":
            name = request.form.get("name")

            relatioship = Relationship.query.filter_by(name=name).all()

            liaison_update = request.form.get("newliaison")
            involvement_update = request.form.get("newinvolvement")

            relatioship.liaison.append(liaison_update)
            relatioship.involvement.append(involvement_update)
            db.session.commit()

    return render_template("dashboard.html", user=user, relatioships=relatioships)


@app.route('/search',methods=['GET', 'POST'])
def search():
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if request.method == "POST":
        searched = request.args.get('searched')
        if searched:
            users=User.query.filter(User.username.contains(searched))
            return render_template("search.html", user=user, users=users)
        else:
            return "No results for your search"
    return render_template("search.html", user=user)


@app.route('/dashboard', methods=['GET', 'POST'])
def upload_wish():
    user_id = session.get("user_id")
    user = User.query.get(user_id)

    if request.method == "POST":
        file = request.files['file']
        filename = file.filename
        file.save(os.path.join('uploads', filename))

        name = request.form.get('name')
        link = request.form.get('link')
        wishlist = request.form.get('wishlist')

        new_wish = Wish(
            image=filename,
            name=name,
            link=link,
            wishlist=wishlist)

        db.session.add(new_wish)
        db.session.commit()

    return render_template("mywishlist.html")

@app.route('/createwishlist', methods=['GET', 'POST'])
def updatewishlist():
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if request.method == "POST":
        new_wishlist = request.form.get("wishlistname")
        new_occasion = request.form.get("newoccasion")
        new_group = request.form.get("newgroup")
        wishes_list = Wish.query.join(Wish.occasion).filter(occasion=new_occasion).all()

        for wish in wishes_list:
            new_wishlist.append(wish)
            # Attach wishlist to a specific group

        specific_group = Group.query.filter_by(name=new_group).all()
        #specific_group.wishes.append(new_wishlist)
    return render_template("dashboard.html")



@app.route('/myevents', methods=['GET', 'POST'])
def create_group():
    user_id = session.get("user_id")
    user = User.query.get(user_id)


    return render_template("groupdashboard.html")







if __name__ == '__main__':
    app.run(debug=True)
