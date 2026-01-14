from flask import Flask, render_template, request, redirect, url_for, Response
from models import db, Hall, Startup, Allocation, SeatChangeRequest
from datetime import datetime
from sqlalchemy.orm import aliased
import csv
from io import StringIO
from flask import session


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://snehankitpatil@localhost/incubation_portal"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
app.secret_key = "dev-secret-key"


#-----------------------------
# login
#-----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]

        startup = Startup.query.filter_by(email=email).first()
        if not startup:
            return "Invalid email", 400

        session["user_id"] = startup.id
        session["role"] = startup.role

        # Redirect based on role
        if startup.role == "admin":
            return redirect("/admin/dashboard")
        else:
            return redirect("/user/dashboard")

    return render_template("login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        return "Forbidden", 403

    return "ADMIN DASHBOARD"



# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
@app.route("/")
def dashboard():
    halls = Hall.query.all()
    data = []

    for hall in halls:
        occupied = (
            db.session.query(db.func.sum(Startup.seats_allocated))
            .filter(
                Startup.hall_id == hall.id,
                Startup.status == "active"
            )
            .scalar()
        ) or 0

        available = hall.total_seats - occupied
        utilization = round(
            (occupied / hall.total_seats) * 100, 1
        ) if hall.total_seats else 0

        data.append({
            "hall": hall,
            "occupied": occupied,
            "available": available,
            "utilization": utilization
        })

    return render_template(
        "dashboard.html",
        data=data
    )

@app.route("/user/dashboard")
def user_dashboard():
    if session.get("role") != "user":
        return "Forbidden", 403

    startup = Startup.query.get(session["user_id"])

    requests = SeatChangeRequest.query.filter_by(
        startup_id=startup.id
    ).order_by(SeatChangeRequest.requested_at.desc()).all()

    return render_template(
        "user_dashboard.html",
        startup=startup,
        requests=requests
    )

# -------------------------------------------------
# REGISTER STARTUP
# -------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    halls = Hall.query.all()

    if request.method == "POST":
        hall = Hall.query.get(request.form["hall_id"])
        seats = int(request.form["seats"])

        occupied = (
            db.session.query(db.func.sum(Startup.seats_allocated))
            .filter(
                Startup.hall_id == hall.id,
                Startup.status == "active"
            )
            .scalar()
        ) or 0

        if seats > (hall.total_seats - occupied):
            return render_template(
                "register.html",
                halls=halls,
                error="Not enough seats available"
            )

        startup = Startup(
            name=request.form["name"],
            founder=request.form["founder"],
            email=request.form["email"],
            phone=request.form["phone"],
            hall_id=hall.id,
            seats_allocated=seats,
            status="applied"
        )

        db.session.add(startup)
        db.session.commit()
        return redirect(url_for("startups"))

    return render_template("register.html", halls=halls)

# -------------------------------------------------
# STARTUPS LIST
# -------------------------------------------------
@app.route("/startups")
def startups():
    latest_request = aliased(SeatChangeRequest)

    startups = (
        db.session.query(Startup, latest_request)
        .outerjoin(
            latest_request,
            db.and_(
                latest_request.startup_id == Startup.id,
                latest_request.status == "pending"
            )
        )
        .all()
    )

    return render_template("startups.html", startups=startups)

# -------------------------------------------------
# HALL DETAIL
# -------------------------------------------------
@app.route("/hall/<int:hall_id>")
def hall_detail(hall_id):
    hall = Hall.query.get_or_404(hall_id)

    startups = Startup.query.filter(
        Startup.hall_id == hall.id,
        Startup.status == "active"
    ).all()

    return render_template("hall_detail.html", hall=hall, startups=startups)

# -------------------------------------------------
# STARTUP LIFECYCLE
# -------------------------------------------------
@app.route("/startup/<int:id>/approve")
def approve(id):
    startup = Startup.query.get_or_404(id)
    startup.status = "approved"
    db.session.commit()
    return redirect("/startups")


@app.route("/startup/<int:id>/activate")
def activate(id):
    startup = Startup.query.get_or_404(id)
    startup.status = "active"

    allocation = Allocation(
        startup_id=startup.id,
        hall_id=startup.hall_id,
        seats=startup.seats_allocated,
        allocated_at=datetime.utcnow()
    )

    db.session.add(allocation)
    db.session.commit()
    return redirect("/startups")


@app.route("/startup/<int:id>/exit")
def exit_startup(id):
    startup = Startup.query.get_or_404(id)
    startup.status = "exited"

    Allocation.query.filter_by(
        startup_id=startup.id,
        released_at=None
    ).update({"released_at": datetime.utcnow()})

    db.session.commit()
    return redirect("/startups")

# -------------------------------------------------
# SEAT CHANGE REQUESTS
# -------------------------------------------------
@app.route("/startup/<int:id>/request-seats", methods=["POST"])
def request_seat_change(id):
    startup = Startup.query.get_or_404(id)

    delta = int(request.form["seats"])
    note = request.form["note"]

    if delta == 0:
        return "Seat change cannot be zero", 400

    existing = SeatChangeRequest.query.filter_by(
        startup_id=startup.id,
        status="pending"
    ).first()

    if existing:
        return "You already have a pending request", 400

    req = SeatChangeRequest(
        startup_id=startup.id,
        current_seats=startup.seats_allocated,
        requested_seats=delta,
        user_note=note,
        requested_at=datetime.utcnow()
    )

    db.session.add(req)
    db.session.commit()
    return redirect("/startups")


@app.route("/seat-requests")
def seat_requests():
    requests = (
        db.session.query(
            SeatChangeRequest,
            Startup.name.label("startup_name")
        )
        .join(Startup, Startup.id == SeatChangeRequest.startup_id)
        .order_by(SeatChangeRequest.requested_at.desc())
        .all()
    )

    return render_template(
        "seat_requests.html",
        requests=requests
    )



@app.route("/seat-requests/<int:id>/approve")
def approve_seat_request(id):
    req = SeatChangeRequest.query.get_or_404(id)
    startup = Startup.query.get_or_404(req.startup_id)
    hall = Hall.query.get_or_404(startup.hall_id)

    delta = req.requested_seats
    new_seats = startup.seats_allocated + delta

    if new_seats < 1:
        return "Invalid seat count", 400

    if delta > 0:
        available = hall.total_seats - hall.occupied_seats
        if delta > available:
            return "Not enough seats available", 400
        hall.occupied_seats += delta
    else:
        hall.occupied_seats += delta

    startup.seats_allocated = new_seats

    req.status = "completed"
    req.decision = "approved"
    req.decided_at = datetime.utcnow()

    db.session.commit()
    return redirect("/seat-requests")



@app.route("/seat-requests/<int:id>/reject")
def reject_seat_request(id):
    req = SeatChangeRequest.query.get_or_404(id)

    req.status = "completed"
    req.decision = "rejected"
    req.decided_at = datetime.utcnow()

    db.session.commit()
    return redirect("/seat-requests")

#---------------------------------------------
#seat history
#---------------------------------------------
@app.route("/seat-requests/history")
def seat_requests_history():
    requests = (
        db.session.query(SeatChangeRequest, Startup.name)
        .join(Startup, Startup.id == SeatChangeRequest.startup_id)
        .filter(SeatChangeRequest.status != "pending")
        .order_by(SeatChangeRequest.decided_at.desc())
        .all()
    )

    return render_template(
        "seat_requests_history.html",
        requests=requests
    )

# -------------------------------------------------
# ALLOCATIONS
# -------------------------------------------------
@app.route("/allocations")
def allocations():
    records = (
        db.session.query(
            Allocation,
            Startup.name.label("startup_name"),
            Hall.name.label("hall_name")
        )
        .join(Startup, Startup.id == Allocation.startup_id)
        .join(Hall, Hall.id == Allocation.hall_id)
        .order_by(Allocation.allocated_at.desc())
        .all()
    )

    return render_template("allocations.html", records=records)

# -------------------------------------------------
# REPORTS
# -------------------------------------------------
@app.route("/reports")
def reports_dashboard():
    return render_template("reports_dashboard.html")


@app.route("/reports/startups")
def report_startups():
    startups = (
        db.session.query(
            Startup,
            Hall.name.label("hall_name")
        )
        .outerjoin(Hall, Hall.id == Startup.hall_id)
        .order_by(Startup.id)
        .all()
    )
    return render_template("report_startups.html", startups=startups)


@app.route("/reports/allocations")
def report_allocations():
    records = (
        db.session.query(
            Allocation,
            Startup.name.label("startup_name"),
            Hall.name.label("hall_name")
        )
        .join(Startup, Startup.id == Allocation.startup_id)
        .join(Hall, Hall.id == Allocation.hall_id)
        .order_by(Allocation.allocated_at.desc())
        .all()
    )
    return render_template("report_allocations.html", records=records)

@app.route("/reports/utilization")
def report_utilization():
    halls = Hall.query.all()
    data = []

    for hall in halls:
        occupied = (
            db.session.query(db.func.sum(Startup.seats_allocated))
            .filter(
                Startup.hall_id == hall.id,
                Startup.status == "active"
            )
            .scalar()
        ) or 0

        data.append({
            "hall": hall,
            "occupied": occupied,
            "available": hall.total_seats - occupied,
            "utilization": round(
                (occupied / hall.total_seats) * 100, 1
            ) if hall.total_seats else 0
        })

    return render_template("report_utilization.html", data=data)

@app.route("/reports/alerts")
def report_alerts():
    halls = Hall.query.all()
    alerts = []

    for hall in halls:
        occupied = (
            db.session.query(db.func.sum(Startup.seats_allocated))
            .filter(
                Startup.hall_id == hall.id,
                Startup.status == "active"
            )
            .scalar()
        ) or 0

        available = hall.total_seats - occupied
        utilization = round(
            (occupied / hall.total_seats) * 100, 1
        ) if hall.total_seats else 0

        if utilization >= 80:
            alerts.append(
                f"{hall.name} is {utilization}% occupied."
            )

        if available == 0:
            alerts.append(
                f"No seats available in {hall.name}."
            )

    return render_template("report_alerts.html", alerts=alerts)

# -------------------------------------------------
# CSV EXPORTS
# -------------------------------------------------
@app.route("/export/startups.csv")
def download_startups_csv():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Startup Name", "Founder", "Email",
        "Phone", "Hall ID", "Seats", "Status"
    ])

    for s in Startup.query.order_by(Startup.id).all():
        writer.writerow([
            s.name, s.founder, s.email,
            s.phone, s.hall_id, s.seats_allocated, s.status
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=startups.csv"
    return response


@app.route("/export/allocations.csv")
def download_allocations_csv():
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Startup", "Hall", "Seats",
        "Allocated At", "Released At", "Event"
    ])

    records = (
        db.session.query(
            Allocation,
            Startup.name.label("startup_name"),
            Hall.name.label("hall_name")
        )
        .join(Startup, Startup.id == Allocation.startup_id)
        .join(Hall, Hall.id == Allocation.hall_id)
        .order_by(Allocation.allocated_at)
        .all()
    )

    for a, startup, hall in records:
        writer.writerow([
            startup,
            hall,
            a.seats,
            a.allocated_at,
            a.released_at or "",
            "Exited" if a.released_at else "Active"
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=allocations.csv"
    return response

@app.route("/reports/utilization.csv")
def export_utilization_csv():
    output = StringIO()
    writer = csv.writer(output)

    # CSV header
    writer.writerow([
        "Hall Name",
        "Total Seats",
        "Occupied Seats",
        "Available Seats",
        "Utilization (%)"
    ])

    halls = Hall.query.all()

    for hall in halls:
        occupied = (
            db.session.query(db.func.sum(Startup.seats_allocated))
            .filter(
                Startup.hall_id == hall.id,
                Startup.status == "active"
            )
            .scalar()
        ) or 0

        available = hall.total_seats - occupied
        utilization = round(
            (occupied / hall.total_seats) * 100, 1
        ) if hall.total_seats else 0

        writer.writerow([
            hall.name,
            hall.total_seats,
            occupied,
            available,
            utilization
        ])

    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )
    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=hall_utilization.csv"

    return response

# -------------------------------------------------
# RUN
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
