# from flask_sqlalchemy import SQLAlchemy

# db = SQLAlchemy()


# class User(db.Model):
#     __tablename__ = "users"
#     id = db.Column(db.Integer, primary_key=True)
#     full_name = db.Column(db.String(150))
#     phone_number = db.Column(db.String(15))
#     password_hash = db.Column(db.String(255))
#     is_activated = db.Column(db.Boolean)
#     created_at = db.Column(db.DateTime)

#     def __repr__(self):
#         return f"{self.full_name} ({self.phone_number})"


# class Task(db.Model):
#     __tablename__ = "tasks"
#     id = db.Column(db.Integer, primary_key=True)
#     task_type = db.Column(db.String(50))
#     title = db.Column(db.String(150))
#     instructions = db.Column(db.Text)
#     reward_amount = db.Column(db.Numeric(6, 2))
#     is_active = db.Column(db.Boolean)
#     created_at = db.Column(db.DateTime)

#     def __repr__(self):
#         return self.title


# class Submission(db.Model):
#     __tablename__ = "submissions"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
#     task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))
#     file_url = db.Column(db.String(255))
#     answer_text = db.Column(db.String(255))
#     status = db.Column(db.String(20))
#     submitted_at = db.Column(db.DateTime)

#     user = db.relationship("User", backref="submissions")
#     task = db.relationship("Task", backref="submissions")

#     def __repr__(self):
#         return f"Submission #{self.id} ({self.status})"


# class Payment(db.Model):
#     __tablename__ = "payments"
#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
#     amount = db.Column(db.Numeric(6, 2))
#     mpesa_receipt = db.Column(db.String(50))
#     status = db.Column(db.String(20))
#     created_at = db.Column(db.DateTime)

#     user = db.relationship("User", backref="payments")

#     def __repr__(self):
#         return f"Payment #{self.id} ({self.status})"

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    phone_number = db.Column(db.String(15))
    password_hash = db.Column(db.String(255))
    is_activated = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return f"{self.full_name} ({self.phone_number})"


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    task_type = db.Column(db.String(50))
    title = db.Column(db.String(150))
    instructions = db.Column(db.Text)
    reward_amount = db.Column(db.Numeric(6, 2))
    is_active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)

    def __repr__(self):
        return self.title


class Submission(db.Model):
    __tablename__ = "submissions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"))
    file_url = db.Column(db.String(255))
    answer_text = db.Column(db.String(255))
    status = db.Column(db.String(20))
    submitted_at = db.Column(db.DateTime)

    user = db.relationship("User", backref=db.backref("submissions", cascade="all, delete-orphan"))
    task = db.relationship("Task", backref="submissions")

    def __repr__(self):
        return f"Submission #{self.id} ({self.status})"


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    amount = db.Column(db.Numeric(6, 2))
    mpesa_receipt = db.Column(db.String(50))
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime)

    user = db.relationship("User", backref=db.backref("payments", cascade="all, delete-orphan"))

    def __repr__(self):
        return f"Payment #{self.id} ({self.status})"