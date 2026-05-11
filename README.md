# Crime Management System
### Built with Python | SQLite3 | Tkinter

A desktop-based Crime Management System for managing criminals, crimes, officers, cases, and evidence — all stored locally using SQLite3 with a dark-themed Tkinter GUI.

---

## Features

- Dashboard with live statistics
- Criminal Records Management (CRUD)
- Crime Logging with severity and status tracking
- Officer Management with badge numbers
- Case Management linked to crimes and officers
- Evidence Vault linked to cases
- Search and filter functionality
- Fully local, no internet required

---

## Project Structure

```
CrimeManagementSystem/
|
|-- crime_management_system.py   # Main application (all-in-one)
|-- crime_management.db          # SQLite database (auto-created on first run)
|-- README.md                    # Project documentation
|-- requirements.txt             # Dependencies
|-- run.bat                      # Windows quick-launch script
```

---

## Requirements

Python 3.7 or higher. No external libraries required.

Built-in modules used:
- tkinter  -- GUI framework
- sqlite3  -- Local database
- datetime -- Date handling
- re       -- Regular expressions

---

## How to Run

Option 1 - Command Line:
  python crime_management_system.py

Option 2 - Windows Quick Launch:
  Double-click run.bat

Option 3 - PyCharm:
  Right-click crime_management_system.py then click Run

---

## Usage Order

Always follow this order when adding new records:

  1. Add Criminals    (required before logging crimes)
  2. Log Crimes       (links to a criminal)
  3. Add Officers     (required before creating cases)
  4. Create Cases     (links a crime + officer)
  5. Add Evidence     (links to a case)

---

## Developer Info

  Language  : Python 3
  GUI       : Tkinter
  Database  : SQLite3
  Platform  : Windows / Mac / Linux
  Version   : 1.0
