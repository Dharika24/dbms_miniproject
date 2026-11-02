import sqlite3
from datetime import date
DB_NAME = "hotel_booking.db"
def connect_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
def setup_database():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY,
                room_type TEXT NOT NULL,
                price_per_night REAL NOT NULL CHECK(price_per_night > 0),
                status TEXT NOT NULL DEFAULT 'Available'
                    CHECK(status IN ('Available', 'Booked'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS guests (
                guest_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL UNIQUE
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                check_in TEXT NOT NULL,
                check_out TEXT NOT NULL,
                total_amount REAL NOT NULL CHECK(total_amount > 0),
                booking_status TEXT NOT NULL DEFAULT 'Confirmed',
                FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
                FOREIGN KEY (room_id) REFERENCES rooms(room_id),
                CHECK(check_out > check_in)
            )
        """)
        conn.executemany("""
            INSERT OR IGNORE INTO rooms(room_id, room_type, price_per_night, status)
            VALUES (?, ?, ?, 'Available')
        """, [
            (101, "Single", 1500),
            (102, "Double", 2500),
            (201, "Deluxe", 4000)
        ])
def show_rooms():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT room_id, room_type, price_per_night, status
            FROM rooms ORDER BY room_id
        """).fetchall()
    print("\nROOM AVAILABILITY")
    print("-" * 54)
    print(f"{'Room ID':<10}{'Type':<12}{'Price/Night':<16}{'Status'}")
    for row in rows:
        print(f"{row[0]:<10}{row[1]:<12}₹{row[2]:<15.0f}{row[3]}")
    print("-" * 54)
def book_room(name, phone, room_id, check_in, check_out):
    start = date.fromisoformat(check_in)
    end = date.fromisoformat(check_out)
    nights = (end - start).days
    if nights <= 0:
        raise ValueError("Check-out date must be after check-in date.")
    with connect_db() as conn:
        room = conn.execute(
            "SELECT price_per_night, status FROM rooms WHERE room_id = ?",
            (room_id,)
        ).fetchone()
        if room is None:
            print("Booking failed: room does not exist.")
            return
        if room[1] != "Available":
            print("Booking failed: room is already booked.")
            return
        conn.execute(
            "INSERT OR IGNORE INTO guests(name, phone) VALUES (?, ?)",
            (name, phone)
        )
        guest_id = conn.execute(
            "SELECT guest_id FROM guests WHERE phone = ?", (phone,)
        ).fetchone()[0]
        total = room[0] * nights
        cursor = conn.execute("""
            INSERT INTO bookings(guest_id, room_id, check_in, check_out, total_amount)
            VALUES (?, ?, ?, ?, ?)
        """, (guest_id, room_id, check_in, check_out, total))
        conn.execute("UPDATE rooms SET status = 'Booked' WHERE room_id = ?", (room_id,))
        booking_id = cursor.lastrowid
    print("\nBOOKING CONFIRMED")
    print(f"Booking ID : {booking_id}")
    print(f"Guest      : {name}")
    print(f"Room       : {room_id}")
    print(f"Stay       : {check_in} to {check_out} ({nights} night(s))")
    print(f"Total      : ₹{total:.2f}")
def show_bookings():
    with connect_db() as conn:
        rows = conn.execute("""
            SELECT b.booking_id, g.name, r.room_id, r.room_type,
                   b.check_in, b.check_out, b.total_amount, b.booking_status
            FROM bookings b
            JOIN guests g ON b.guest_id = g.guest_id
            JOIN rooms r ON b.room_id = r.room_id
            ORDER BY b.booking_id
        """).fetchall()
    print("\nBOOKING REGISTER")
    print("-" * 100)
    print(f"{'ID':<5}{'Guest':<18}{'Room':<8}{'Type':<10}{'Check-in':<13}{'Check-out':<13}{'Amount':<12}{'Status'}")
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<18}{row[2]:<8}{row[3]:<10}{row[4]:<13}{row[5]:<13}₹{row[6]:<11.2f}{row[7]}")
    if not rows:
        print("No bookings found.")
    print("-" * 100)
def cancel_booking(booking_id):
    with connect_db() as conn:
        row = conn.execute(
            "SELECT room_id FROM bookings WHERE booking_id = ? AND booking_status = 'Confirmed'",
            (booking_id,)
        ).fetchone()
        if row is None:
            print("Cancellation failed: confirmed booking not found.")
            return
        conn.execute(
            "UPDATE bookings SET booking_status = 'Cancelled' WHERE booking_id = ?",
            (booking_id,)
        )
        conn.execute("UPDATE rooms SET status = 'Available' WHERE room_id = ?", (row[0],))
    print(f"Booking {booking_id} cancelled successfully.")
def main():
    setup_database()
    while True:
        print("\\n=== HOTEL ROOM BOOKING SYSTEM ===")
        print("1. View rooms")
        print("2. Book a room")
        print("3. View bookings")
        print("4. Cancel booking")
        print("5. Exit")
        choice = input("Enter choice: ").strip()
        if choice == "1":
            show_rooms()
        elif choice == "2":
            try:
                name = input("Guest name: ").strip()
                phone = input("Phone: ").strip()
                room_id = int(input("Room ID: "))
                check_in = input("Check-in (YYYY-MM-DD): ").strip()
                check_out = input("Check-out (YYYY-MM-DD): ").strip()
                book_room(name, phone, room_id, check_in, check_out)
            except (ValueError, sqlite3.IntegrityError) as error:
                print(f"Input/database error: {error}")
        elif choice == "3":
            show_bookings()
        elif choice == "4":
            try:
                cancel_booking(int(input("Booking ID to cancel: ")))
            except ValueError:
                print("Please enter a valid booking ID.")
        elif choice == "5":
            print("Thank you for using the system.")
            break
        else:
            print("Invalid choice. Please try again.")
if __name__ == "__main__":
    main()
