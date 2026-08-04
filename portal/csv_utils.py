"""Utilities for the bulk CSV student upload.

Expected format (UTF-8), first row optional header:

    roll_number,name
    21CS1001,Arjun Kumar
    21CS1002,Priya Sharma
"""
import csv
import io

HEADER_WORDS = {"roll", "rollno", "roll_number", "roll number", "username", "regno", "reg_no"}


def parse_students_csv(data):
    """Return a list of (roll_number, name) tuples from raw CSV bytes."""
    text = data.decode("utf-8-sig", errors="replace")
    rows = []
    reader = csv.reader(io.StringIO(text))
    first_row = True
    for row in reader:
        if not row or not row[0].strip():
            continue
        if first_row:
            first_row = False
            if row[0].strip().lower() in HEADER_WORDS:
                continue
        roll = row[0].strip().upper()
        name = row[1].strip() if len(row) > 1 and row[1].strip() else roll
        rows.append((roll, name))
    return rows
