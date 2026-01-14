CREATE TABLE spaces (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL,
    occupied BOOLEAN DEFAULT FALSE,
    equipment TEXT
);

INSERT INTO spaces (name, capacity, occupied, equipment)
VALUES
('Hall A', 50, TRUE, 'Projector, AC, Whiteboard'),
('Hall B', 30, FALSE, 'AC, WiFi'),
('Room 101', 10, TRUE, 'WiFi'),
('Room 102', 8, FALSE, 'WiFi, Printer');

SELECT * FROM spaces;

CREATE TABLE halls (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    total_seats INTEGER NOT NULL,
    occupied_seats INTEGER DEFAULT 0
);

INSERT INTO halls (name, total_seats)
VALUES
('Incubation Hall 1', 50),
('Incubation Hall 2', 30);

CREATE TABLE startups (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    founder TEXT,
    email TEXT,
    phone TEXT,
    hall_id INTEGER REFERENCES halls(id),
    seats_allocated INTEGER
);

ALTER TABLE startups
ADD COLUMN status TEXT DEFAULT 'applied';

ALTER TABLE startups
ADD COLUMN role VARCHAR(20) DEFAULT 'user';


SELECT * FROM startups 

CREATE TABLE seats (
    id SERIAL PRIMARY KEY,
    hall INTEGER NOT NULL,        -- 1 or 2
    seat_number INTEGER NOT NULL,
    occupied BOOLEAN DEFAULT FALSE
);

-- Hall 1
INSERT INTO seats (hall, seat_number)
SELECT 1, generate_series(1, 50);

-- Hall 2
INSERT INTO seats (hall, seat_number)
SELECT 2, generate_series(1, 30);


SELECT * FROM seats


CREATE TABLE allocations (
    id SERIAL PRIMARY KEY,
    startup_id INTEGER,
    hall_id INTEGER,
    seats INTEGER,
    allocated_at TIMESTAMP DEFAULT NOW(),
    released_at TIMESTAMP
);

ALTER TABLE allocations ADD COLUMN reason TEXT;

SELECT id, name, hall_id, seats_allocated, status
FROM startups;

SELECT * FROM allocations

CREATE TABLE seat_change_requests (
    id SERIAL PRIMARY KEY,
    startup_id INTEGER REFERENCES startups(id),
    requested_seats INTEGER NOT NULL,
    current_seats INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW()
);

ALTER TABLE seat_change_requests
ADD COLUMN user_note TEXT,
ADD COLUMN decided_at TIMESTAMP;

DROP TABLE seat_change_requests

ALTER TABLE seat_change_requests
ADD COLUMN decision VARCHAR(20);

SELECT * FROM seat_change_requests
