from flask import Blueprint, render_template

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/")
def dashboard():
    # Temporary placeholder page
    return render_template("admin/learners_list.html")