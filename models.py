from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
    
class Hall(db.Model):
    __tablename__ = "halls"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    total_seats = db.Column(db.Integer)
    occupied_seats = db.Column(db.Integer, default=0)


class Startup(db.Model):
    __tablename__ = "startups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    founder = db.Column(db.String(200))
    email = db.Column(db.String(200))
    phone = db.Column(db.String(50))

    status = db.Column(db.String(20), default="applied")  # NEW
    hall_id = db.Column(db.Integer, db.ForeignKey("halls.id"))
    seats_allocated = db.Column(db.Integer)
    role = db.Column(db.String(20), default="user")



class Allocation(db.Model):
    __tablename__ = "allocations"

    id = db.Column(db.Integer, primary_key=True)
    startup_id = db.Column(db.Integer)
    hall_id = db.Column(db.Integer)
    seats = db.Column(db.Integer)
    allocated_at = db.Column(db.DateTime)
    released_at = db.Column(db.DateTime)

class SeatChangeRequest(db.Model):
    __tablename__ = "seat_change_requests"

    id = db.Column(db.Integer, primary_key=True)

    startup_id = db.Column(db.Integer, nullable=False)

    current_seats = db.Column(db.Integer, nullable=False)
    requested_seats = db.Column(db.Integer, nullable=False)

    user_note = db.Column(db.Text)

    status = db.Column(
        db.String(20),
        default="pending"   # pending → completed
    )

    decision = db.Column(
        db.String(20)       # approved / rejected
    )

    requested_at = db.Column(db.DateTime)
    decided_at = db.Column(db.DateTime)
