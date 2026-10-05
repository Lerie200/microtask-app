import os
import re
import uuid
import bcrypt
from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from werkzeug.utils import secure_filename
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token,
    jwt_required, get_jwt_identity
)
from flasgger import Swagger
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from markupsafe import Markup
from dotenv import load_dotenv

from db import get_connection, get_dict_cursor
from intasend_service import initiate_stk_push
from models import db, User, Task, Submission, Payment

ACTIVATION_FEE = 1

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "webm", "mp3", "wav", "m4a", "ogg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("ADMIN_SESSION_SECRET", "change-this-admin-secret")
CORS(app, resources={
        r"/api/*": {
        "origins": [
            "http://localhost:4200",
            "http://127.0.0.1:4200",
            "https://microtask-frontend.onrender.com"
        ]
    }

})
app.config["SWAGGER"] = {
    "title": "Microtask App API",
    "uiversion": 3,
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter: Bearer <your_access_token>"
        }
    }
}
swagger = Swagger(app)

# ------------------------------------------------------------------
# Admin panel setup (Flask-Admin, uses SQLAlchemy on the same DB)
# ------------------------------------------------------------------
# SQLAlchemy (used only by the admin panel) needs the driver named explicitly;
# psycopg2's own connect() calls elsewhere in this file use DATABASE_URL as-is.
_sqlalchemy_uri = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+psycopg2://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = _sqlalchemy_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

LOGIN_PAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Admin Login</title>
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0F766E, #115E59);
           min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
    .card { background: white; padding: 36px; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); width: 320px; }
    h2 { color: #0F766E; text-align: center; margin-bottom: 20px; }
    input { width: 100%; padding: 10px; margin-bottom: 14px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; }
    button { width: 100%; padding: 10px; background: #0F766E; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
    button:hover { background: #115E59; }
    .error { color: #DC2626; text-align: center; margin-bottom: 12px; font-size: 0.9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Admin Login</h2>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="post">
      <input type="text" name="username" placeholder="Username" required>
      <input type="password" name="password" placeholder="Password" required>
      <button type="submit">Log In</button>
    </form>
  </div>
</body>
</html>
"""


class SecureAdminIndexView(AdminIndexView):
    @expose("/")
    def index(self):
        if not session.get("is_admin"):
            return redirect(url_for(".login"))
        return super().index()

    @expose("/login", methods=["GET", "POST"])
    def login(self):
        error = None
        if request.method == "POST":
            if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
                session["is_admin"] = True
                return redirect(url_for(".index"))
            error = "Invalid username or password."
        return render_template_string(LOGIN_PAGE_HTML, error=error)

    @expose("/logout")
    def logout(self):
        session.pop("is_admin", None)
        return redirect(url_for(".login"))


class SecureModelView(ModelView):
    def is_accessible(self):
        return session.get("is_admin", False)

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("admin.login"))


class SubmissionAdminView(SecureModelView):
    column_list = ("id", "user", "task", "status", "photo", "answer_text", "submitted_at")
    column_editable_list = ("status",)  # lets you approve/reject inline from the list view
    form_columns = ("status",)  # only status is editable via the edit form
    form_choices = {
        "status": [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ]
    }

    def _photo_formatter(view, context, model, name):
        if not model.file_url:
            return ""
        url = f"/uploads/{model.file_url}"
        return Markup(f'<a href="{url}" target="_blank"><img src="{url}" style="height:60px;border-radius:6px;"></a>')

    column_formatters = {"photo": _photo_formatter}


class UserAdminView(SecureModelView):
    column_list = ("id", "full_name", "phone_number", "is_activated", "latest_payment", "created_at")
    column_exclude_list = ("password_hash",)
    form_columns = ("full_name", "phone_number", "is_activated")
    column_labels = {"is_activated": "Paid / Activated", "latest_payment": "Payment Details"}

    def _latest_payment_formatter(view, context, model, name):
        if not model.payments:
            return Markup('<span style="color:#DC2626;">Not paid</span>')
        latest = sorted(model.payments, key=lambda p: p.created_at or 0, reverse=True)[0]
        color = "#16A34A" if latest.status == "success" else "#DC2626" if latest.status == "failed" else "#F59E0B"
        return Markup(
            f'<span style="color:{color};font-weight:600;">KSh {latest.amount} ({latest.status})</span><br>'
            f'<small style="color:#64748b;">{latest.created_at.strftime("%d %b %Y, %H:%M") if latest.created_at else ""}</small>'
        )

    column_formatters = {"latest_payment": _latest_payment_formatter}


class TaskAdminView(SecureModelView):
    column_list = ("id", "title", "task_type", "reward_amount", "is_active")


class PaymentAdminView(SecureModelView):
    column_list = ("id", "user", "amount", "mpesa_receipt", "status", "created_at")


admin = Admin(app, name="Microtask Admin", template_mode="bootstrap4", index_view=SecureAdminIndexView())
admin.add_view(UserAdminView(User, db.session))
admin.add_view(TaskAdminView(Task, db.session))
admin.add_view(SubmissionAdminView(Submission, db.session))
admin.add_view(PaymentAdminView(Payment, db.session))

# home on render
@app.route("/")
def home():
    return {"message": "Microtask API is running"}


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_FOLDER, filename)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
jwt = JWTManager(app)

PHONE_REGEX = re.compile(r"^\+?254\d{9}$|^0\d{9}$")  # accepts 07XXXXXXXX or +2547XXXXXXXX


# ------------------------------------------------------------------
# Registration
# ------------------------------------------------------------------
@app.route("/api/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            full_name:
              type: string
              example: Test User
            phone_number:
              type: string
              example: "0712345678"
            password:
              type: string
              example: test123
            confirm_password:
              type: string
              example: test123
    responses:
      201:
        description: Registration successful
      400:
        description: Validation error
      409:
        description: Phone number already registered
    """
    data = request.get_json(force=True)

    full_name = (data.get("full_name") or "").strip()
    phone_number = (data.get("phone_number") or "").strip()
    password = data.get("password") or ""
    confirm_password = data.get("confirm_password") or ""

    # --- Validation ---
    if not full_name or not phone_number or not password:
        return jsonify({"error": "All fields are required."}), 400

    if not PHONE_REGEX.match(phone_number):
        return jsonify({"error": "Enter a valid phone number, e.g. 0712345678."}), 400

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    conn = get_connection()
    cur = get_dict_cursor(conn)

    try:
        cur.execute("SELECT id FROM users WHERE phone_number = %s", (phone_number,))
        if cur.fetchone():
            return jsonify({"error": "This phone number is already registered."}), 409

        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        cur.execute(
            """
            INSERT INTO users (full_name, phone_number, password_hash, is_activated)
            VALUES (%s, %s, %s, FALSE)
            RETURNING id, full_name, phone_number, is_activated
            """,
            (full_name, phone_number, password_hash),
        )
        new_user = cur.fetchone()
        conn.commit()

        return jsonify({
            "message": "Registration successful. Please activate your account to continue.",
            "user": new_user
        }), 201

    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------
# Login
# ------------------------------------------------------------------
@app.route("/api/login", methods=["POST"])
def login():
    """
    Log in and receive a JWT access token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            phone_number:
              type: string
              example: "0712345678"
            password:
              type: string
              example: test123
    responses:
      200:
        description: Login successful, returns access_token
      401:
        description: Invalid credentials
    """
    data = request.get_json(force=True)
    phone_number = (data.get("phone_number") or "").strip()
    password = data.get("password") or ""

    conn = get_connection()
    cur = get_dict_cursor(conn)

    try:
        cur.execute(
            "SELECT id, full_name, phone_number, password_hash, is_activated FROM users WHERE phone_number = %s",
            (phone_number,),
        )
        user = cur.fetchone()

        if not user:
            return jsonify({"error": "This phone number is not registered."}), 404

        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            return jsonify({"error": "Incorrect password."}), 401

        access_token = create_access_token(identity=str(user["id"]))

        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "phone_number": user["phone_number"],
                "is_activated": user["is_activated"],
            }
        }), 200

    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------
# Example protected route (gated by activation) — tasks come next
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# Trigger the activation payment (STK Push)
# ------------------------------------------------------------------
@app.route("/api/pay/activate", methods=["POST"])
@jwt_required()
def pay_activate():
    """
    Trigger an M-Pesa STK Push (via IntaSend) to pay the KSh 1 activation fee
    ---
    tags:
      - Payments
    security:
      - Bearer: []
    responses:
      200:
        description: STK Push sent to the user's phone
      400:
        description: Already activated, or IntaSend request failed
    """
    user_id = int(get_jwt_identity())

    conn = get_connection()
    cur = get_dict_cursor(conn)

    try:
        cur.execute("SELECT phone_number, is_activated FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if not user:
            return jsonify({"error": "User not found."}), 404

        if user["is_activated"]:
            return jsonify({"message": "Account is already activated."}), 200

        # Record a pending payment row first, so the callback has something to update
        cur.execute(
            "INSERT INTO payments (user_id, amount, status) VALUES (%s, %s, 'pending') RETURNING id",
            (user_id, ACTIVATION_FEE),
        )
        payment_id = cur.fetchone()["id"]
        conn.commit()

        intasend_response = initiate_stk_push(
            phone_number=user["phone_number"],
            amount=ACTIVATION_FEE,
            email=f"{user['phone_number']}@microtask.app",  # placeholder — you don't collect email at registration
            narrative=f"activation-{payment_id}",
        )

        # Store IntaSend's invoice_id so the webhook can match this payment row later
        invoice_id = intasend_response.get("invoice", {}).get("invoice_id")
        if invoice_id:
            cur.execute(
                "UPDATE payments SET mpesa_receipt = %s WHERE id = %s",
                (invoice_id, payment_id),
            )
            conn.commit()

        return jsonify({
            "message": "Check your phone and enter your M-Pesa PIN to complete activation.",
            "intasend_response": intasend_response
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to initiate payment: {str(e)}"}), 400

    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------
# Daraja calls this automatically after the user approves/cancels
# ------------------------------------------------------------------
@app.route("/api/payments/callback", methods=["POST"])
def payment_callback():
    """
    IntaSend calls this endpoint automatically after payment
    (not called manually — no Swagger auth needed)
    ---
    tags:
      - Payments
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          example:
            invoice_id: "DMO2PR9"
            state: "COMPLETE"
            provider: "M-PESA"
            charges: "0.00"
            net_amount: "1.00"
            currency: "KES"
            value: "300.00"
            account: "254708374149"
            api_ref: "activation-12"
    responses:
      200:
        description: Callback received
    """
    data = request.get_json(force=True)
    CHALLENGE_SECRET = os.getenv("INTASEND_CHALLENGE_SECRET")
    if data.get("challenge") != CHALLENGE_SECRET:
        print("Webhook challenge mismatch — rejecting.")
        return jsonify({"error": "Invalid challenge"}), 403


    print("INTASEND CALLBACK RECEIVED:", data)  # helpful for debugging in your terminal

    try:
        invoice_id = data.get("invoice_id")
        state = data.get("state")  # PENDING / COMPLETE / FAILED / PROCESSING

        conn = get_connection()
        cur = get_dict_cursor(conn)

        if state == "COMPLETE":
            # Find the payment row by the invoice_id we stored when initiating the push
            cur.execute(
                "SELECT user_id FROM payments WHERE mpesa_receipt = %s",
                (invoice_id,),
            )
            payment = cur.fetchone()
            print(f"DEBUG: looked up invoice_id={invoice_id!r}, found: {payment}")

            if payment:
                cur.execute(
                    "UPDATE users SET is_activated = TRUE WHERE id = %s",
                    (payment["user_id"],),
                )
                cur.execute(
                    "UPDATE payments SET status = 'success' WHERE mpesa_receipt = %s",
                    (invoice_id,),
                )
                print(f"DEBUG: rows updated in payments: {cur.rowcount}")
                conn.commit()
            else:
                print("DEBUG: no matching payment row — update skipped")


        elif state == "FAILED":
            cur.execute(
                "UPDATE payments SET status = 'failed' WHERE mpesa_receipt = %s",
                (invoice_id,),
            )
            conn.commit()

        cur.close()
        conn.close()

    except (KeyError, TypeError) as e:
        print("Error parsing IntaSend callback:", e)

    # Always return 200, or IntaSend will retry the callback repeatedly
    return jsonify({"message": "Callback received"}), 200


@app.route("/api/tasks", methods=["GET"])
@jwt_required()
def list_tasks():
    """
    List available tasks (requires activated account)
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: List of tasks
      403:
        description: Account not activated
    """
    user_id = int(get_jwt_identity())

    conn = get_connection()
    cur = get_dict_cursor(conn)
    try:
        cur.execute("SELECT is_activated FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if not user or not user["is_activated"]:
            return jsonify({"error": "Account not activated. Please pay the activation fee first."}), 403

        cur.execute(
            """
            SELECT
                t.id, t.task_type, t.title, t.instructions, t.reward_amount,
                s.status AS submission_status
            FROM tasks t
            LEFT JOIN LATERAL (
                SELECT status FROM submissions
                WHERE submissions.task_id = t.id AND submissions.user_id = %s
                ORDER BY submitted_at DESC
                LIMIT 1
            ) s ON TRUE
            WHERE t.is_active = TRUE
            ORDER BY t.id
            """,
            (user_id,),
        )
        tasks = cur.fetchall()
        return jsonify({"tasks": tasks}), 200

    finally:
        cur.close()
        conn.close()


# ------------------------------------------------------------------
# Submit a completed task (starting with photo uploads)
# ------------------------------------------------------------------
@app.route("/api/submissions", methods=["POST"])
@jwt_required()
def submit_task():
    """
    Submit a completed task (file upload OR a text-based answer)
    ---
    tags:
      - Submissions
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: task_id
        type: integer
        required: true
      - in: formData
        name: file
        type: file
        required: false
      - in: formData
        name: answer_text
        type: string
        required: false
    responses:
      201:
        description: Submission recorded
      400:
        description: Missing both file and answer_text, or invalid file
      403:
        description: Account not activated
    """
    user_id = int(get_jwt_identity())

    conn = get_connection()
    cur = get_dict_cursor(conn)

    try:
        cur.execute("SELECT is_activated FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user or not user["is_activated"]:
            return jsonify({"error": "Account not activated."}), 403

        task_id = request.form.get("task_id")
        if not task_id:
            return jsonify({"error": "task_id is required."}), 400

        answer_text = request.form.get("answer_text")
        unique_name = None

        has_file = "file" in request.files and request.files["file"].filename != ""

        if has_file:
            file = request.files["file"]
            if not allowed_file(file.filename):
                return jsonify({"error": "Invalid file type."}), 400
            original_name = secure_filename(file.filename)
            unique_name = f"{uuid.uuid4().hex}_{original_name}"
            file.save(os.path.join(UPLOAD_FOLDER, unique_name))
        elif not answer_text:
            return jsonify({"error": "Either a file or an answer_text is required."}), 400

        cur.execute(
            """
            INSERT INTO submissions (user_id, task_id, file_url, answer_text, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id, status, submitted_at
            """,
            (user_id, task_id, unique_name, answer_text),
        )
        submission = cur.fetchone()
        conn.commit()

        return jsonify({
            "message": "Task submitted successfully. Awaiting review.",
            "submission": submission
        }), 201

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    app.run(debug=True, port=5000)