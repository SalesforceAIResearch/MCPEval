import os
import sqlite3
from typing import Dict, Any, Optional, Literal

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_db() -> None:
    conn = _get_connection()
    cur = conn.cursor()

    # -- Tables ----------------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id            INTEGER PRIMARY KEY,
            name          TEXT UNIQUE NOT NULL,
            location      TEXT NOT NULL,
            budget        REAL NOT NULL,
            head_employee_id INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id            INTEGER PRIMARY KEY,
            first_name    TEXT NOT NULL,
            last_name     TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            department_id INTEGER REFERENCES departments(id),
            manager_id    INTEGER REFERENCES employees(id),
            title         TEXT NOT NULL,
            hire_date     TEXT NOT NULL,
            salary        REAL NOT NULL,
            status        TEXT NOT NULL DEFAULT 'active'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id            INTEGER PRIMARY KEY,
            employee_id   INTEGER NOT NULL REFERENCES employees(id),
            leave_type    TEXT NOT NULL,
            start_date    TEXT NOT NULL,
            end_date      TEXT NOT NULL,
            status        TEXT NOT NULL DEFAULT 'pending',
            reason        TEXT,
            approved_by   INTEGER REFERENCES employees(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS performance_reviews (
            id            INTEGER PRIMARY KEY,
            employee_id   INTEGER NOT NULL REFERENCES employees(id),
            reviewer_id   INTEGER NOT NULL REFERENCES employees(id),
            review_period TEXT NOT NULL,
            rating        INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comments      TEXT,
            review_date   TEXT NOT NULL
        )
    """)

    # -- Seed: departments -----------------------------------------------------

    departments = [
        (1, "Engineering",      "Building A, Floor 3",  2500000.00, 1),
        (2, "Marketing",        "Building B, Floor 1",  1200000.00, 6),
        (3, "Sales",            "Building B, Floor 2",  1800000.00, 10),
        (4, "Human Resources",  "Building A, Floor 1",   800000.00, 14),
        (5, "Finance",          "Building C, Floor 1",   900000.00, 17),
        (6, "Operations",       "Building C, Floor 2",  1100000.00, 21),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO departments (id, name, location, budget, head_employee_id) VALUES (?, ?, ?, ?, ?)",
        departments,
    )

    # -- Seed: employees -------------------------------------------------------
    # Hierarchy per department:
    #   Department Head (VP/Director) -> Team Lead (Senior/Lead) -> IC

    employees = [
        # --- Engineering (dept 1) ---
        # Head
        (1,  "Alice",   "Chen",      "alice.chen@company.com",       1, None, "VP of Engineering",        "2018-03-15", 195000.00, "active"),
        # Team Leads
        (2,  "Bob",     "Martinez",  "bob.martinez@company.com",     1, 1,    "Senior Engineering Manager","2019-06-01", 165000.00, "active"),
        (3,  "Carol",   "Johnson",   "carol.johnson@company.com",    1, 1,    "Lead Software Engineer",   "2019-09-20", 155000.00, "active"),
        # ICs under Bob
        (4,  "David",   "Kim",       "david.kim@company.com",        1, 2,    "Software Engineer",        "2021-01-10", 120000.00, "active"),
        (5,  "Elena",   "Popov",     "elena.popov@company.com",      1, 2,    "Software Engineer",        "2021-07-22", 115000.00, "on_leave"),
        # ICs under Carol
        (25, "Nathan",  "Brooks",    "nathan.brooks@company.com",    1, 3,    "Software Engineer",        "2022-02-14", 112000.00, "active"),
        (26, "Olivia",  "Ward",      "olivia.ward@company.com",      1, 3,    "Junior Software Engineer", "2023-06-05", 95000.00,  "active"),
        (27, "Patrick", "Hughes",    "patrick.hughes@company.com",   1, 3,    "DevOps Engineer",          "2022-08-15", 130000.00, "active"),

        # --- Marketing (dept 2) ---
        # Head
        (6,  "Fatima",  "Al-Rashid", "fatima.alrashid@company.com",  2, None, "Director of Marketing",    "2019-01-08", 160000.00, "active"),
        # Team Lead
        (7,  "George",  "Nguyen",    "george.nguyen@company.com",    2, 6,    "Senior Marketing Manager", "2020-03-15", 130000.00, "active"),
        # ICs
        (8,  "Hannah",  "Lee",       "hannah.lee@company.com",       2, 7,    "Marketing Specialist",     "2021-11-01", 85000.00,  "active"),
        (9,  "Ivan",    "Petrov",    "ivan.petrov@company.com",      2, 7,    "Content Strategist",       "2022-04-18", 82000.00,  "active"),
        (28, "Quinn",   "Foster",    "quinn.foster@company.com",     2, 7,    "Marketing Analyst",        "2023-01-09", 78000.00,  "active"),

        # --- Sales (dept 3) ---
        # Head
        (10, "Julia",   "Smith",     "julia.smith@company.com",      3, None, "VP of Sales",              "2018-07-20", 185000.00, "active"),
        # Team Lead
        (11, "Kevin",   "O'Brien",   "kevin.obrien@company.com",     3, 10,   "Senior Sales Manager",     "2019-11-12", 140000.00, "active"),
        # ICs
        (12, "Lisa",    "Wang",      "lisa.wang@company.com",        3, 11,   "Account Executive",        "2021-05-03", 95000.00,  "active"),
        (13, "Marcus",  "Brown",     "marcus.brown@company.com",     3, 11,   "Sales Representative",     "2022-08-14", 78000.00,  "inactive"),
        (29, "Rachel",  "Cooper",    "rachel.cooper@company.com",    3, 11,   "Account Executive",        "2022-10-01", 92000.00,  "active"),
        (30, "Samuel",  "Reed",      "samuel.reed@company.com",     3, 11,   "Sales Representative",     "2023-03-20", 75000.00,  "active"),

        # --- Human Resources (dept 4) ---
        # Head
        (14, "Nancy",   "Taylor",    "nancy.taylor@company.com",     4, None, "Director of HR",           "2017-11-05", 155000.00, "active"),
        # Team Lead
        (15, "Oscar",   "Garcia",    "oscar.garcia@company.com",     4, 14,   "Senior HR Manager",        "2020-02-10", 115000.00, "active"),
        # ICs
        (16, "Priya",   "Sharma",    "priya.sharma@company.com",     4, 15,   "HR Specialist",            "2021-09-01", 75000.00,  "on_leave"),

        # --- Finance (dept 5) ---
        # Head
        (17, "Robert",  "Davis",     "robert.davis@company.com",     5, None, "Director of Finance",      "2018-05-22", 170000.00, "active"),
        # Team Lead
        (18, "Sandra",  "Wilson",    "sandra.wilson@company.com",    5, 17,   "Senior Financial Analyst",  "2019-10-14", 125000.00, "active"),
        # ICs
        (19, "Thomas",  "Anderson",  "thomas.anderson@company.com",  5, 18,   "Financial Analyst",        "2021-03-08", 90000.00,  "active"),
        (20, "Uma",     "Patel",     "uma.patel@company.com",        5, 18,   "Accountant",               "2022-01-17", 80000.00,  "active"),

        # --- Operations (dept 6) ---
        # Head
        (21, "Victor",  "Lopez",     "victor.lopez@company.com",     6, None, "Director of Operations",   "2018-09-10", 160000.00, "active"),
        # Team Lead
        (22, "Wendy",   "Clark",     "wendy.clark@company.com",      6, 21,   "Senior Operations Manager","2020-06-25", 120000.00, "active"),
        # ICs
        (23, "Xavier",  "Reyes",     "xavier.reyes@company.com",     6, 22,   "Operations Analyst",       "2021-12-01", 82000.00,  "active"),
        (24, "Yuki",    "Tanaka",    "yuki.tanaka@company.com",      6, 22,   "Logistics Coordinator",    "2022-05-30", 72000.00,  "inactive"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO employees "
        "(id, first_name, last_name, email, department_id, manager_id, title, hire_date, salary, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        employees,
    )

    # -- Seed: leave_requests --------------------------------------------------

    leave_requests = [
        (1,  5,  "sick",      "2025-03-10", "2025-03-14", "approved",  "Flu recovery",                         2),
        (2,  4,  "vacation",  "2025-06-01", "2025-06-10", "approved",  "Summer vacation trip",                  2),
        (3,  8,  "personal",  "2025-04-15", "2025-04-16", "approved",  "Family event",                         7),
        (4,  12, "vacation",  "2025-07-20", "2025-07-31", "pending",   "Annual leave",                         None),
        (5,  16, "parental",  "2025-05-01", "2025-08-01", "approved",  "Parental leave - new baby",            15),
        (6,  19, "sick",      "2025-02-20", "2025-02-21", "approved",  "Doctor appointment and recovery",      18),
        (7,  23, "vacation",  "2025-08-10", "2025-08-17", "pending",   "Beach holiday",                        None),
        (8,  9,  "personal",  "2025-03-28", "2025-03-28", "rejected",  "Concert attendance",                   7),
        (9,  25, "vacation",  "2025-09-01", "2025-09-12", "pending",   "European trip",                        None),
        (10, 3,  "sick",      "2025-01-15", "2025-01-17", "approved",  "Back pain treatment",                  1),
        (11, 20, "vacation",  "2025-05-20", "2025-05-23", "approved",  "Long weekend getaway",                 18),
        (12, 29, "sick",      "2025-04-02", "2025-04-03", "approved",  "Migraine",                             11),
        (13, 27, "personal",  "2025-06-15", "2025-06-16", "pending",   "Moving to new apartment",              None),
        (14, 30, "vacation",  "2025-07-01", "2025-07-05", "rejected",  "Short trip - overlaps with team event", 11),
        (15, 22, "sick",      "2025-03-05", "2025-03-06", "approved",  "Cold and fever",                       21),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO leave_requests "
        "(id, employee_id, leave_type, start_date, end_date, status, reason, approved_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        leave_requests,
    )

    # -- Seed: performance_reviews ---------------------------------------------

    performance_reviews = [
        (1,  4,  2,  "2024-H2", 4, "Strong technical skills, good team collaboration. Delivered key features on time.",                  "2025-01-15"),
        (2,  5,  2,  "2024-H2", 3, "Solid work but needs to improve communication with stakeholders.",                                   "2025-01-15"),
        (3,  25, 3,  "2024-H2", 4, "Excellent problem-solving ability. Proactively identifies and resolves issues.",                      "2025-01-20"),
        (4,  26, 3,  "2024-H2", 3, "Good progress for a junior engineer. Should take on more complex tasks.",                            "2025-01-20"),
        (5,  27, 3,  "2024-H2", 5, "Exceptional work on CI/CD pipeline. Reduced deployment time by 40%.",                                "2025-01-20"),
        (6,  8,  7,  "2024-H2", 4, "Creative campaigns with measurable results. Increased engagement by 25%.",                           "2025-01-18"),
        (7,  9,  7,  "2024-H2", 3, "Content quality is good, but needs to publish more consistently.",                                   "2025-01-18"),
        (8,  12, 11, "2024-H2", 5, "Top performer - exceeded quota by 130%. Excellent client relationships.",                             "2025-01-22"),
        (9,  13, 11, "2024-H2", 2, "Below target performance. Needs improvement in client follow-up and pipeline management.",            "2025-01-22"),
        (10, 29, 11, "2024-H2", 4, "Strong first year. Quickly ramped up and closed several key accounts.",                               "2025-01-22"),
        (11, 16, 15, "2024-H2", 4, "Handled sensitive situations with professionalism. Well-liked across departments.",                   "2025-01-25"),
        (12, 19, 18, "2024-H2", 3, "Accurate work but could take more initiative on process improvements.",                              "2025-01-25"),
        (13, 20, 18, "2024-H2", 4, "Meticulous attention to detail. Zero errors in quarterly reconciliation.",                            "2025-01-25"),
        (14, 23, 22, "2024-H2", 3, "Meets expectations. Should develop deeper analytical skills.",                                       "2025-01-28"),
        (15, 24, 22, "2024-H2", 2, "Inconsistent attendance affected deliverables. Needs significant improvement.",                       "2025-01-28"),
        (16, 4,  2,  "2024-H1", 3, "Adequate performance with room for growth. Should focus on code review quality.",                    "2024-07-15"),
        (17, 12, 11, "2024-H1", 4, "Strong sales numbers. Good relationship building with enterprise clients.",                          "2024-07-20"),
        (18, 8,  7,  "2024-H1", 3, "Steady contributor. Campaigns met expectations but lacked innovation.",                              "2024-07-18"),
        (19, 28, 7,  "2024-H2", 3, "Good analytical work. Needs to improve presentation of insights to leadership.",                     "2025-01-18"),
        (20, 30, 11, "2024-H2", 3, "Promising start. Needs to improve cold-calling confidence and objection handling.",                   "2025-01-22"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO performance_reviews "
        "(id, employee_id, reviewer_id, review_period, rating, comments, review_date) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        performance_reviews,
    )

    conn.commit()
    conn.close()


# Initialise the database on module load
_init_db()

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("HR Management")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_departments() -> Dict[str, Any]:
    """
    List all departments with their headcount (number of active employees).
    """
    try:
        conn = _get_connection()
        rows = conn.execute("""
            SELECT d.id, d.name, d.location, d.budget,
                   COUNT(CASE WHEN e.status = 'active' THEN 1 END) AS headcount
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            GROUP BY d.id
            ORDER BY d.id
        """).fetchall()
        conn.close()

        departments = [
            {
                "id": r["id"],
                "name": r["name"],
                "location": r["location"],
                "budget": r["budget"],
                "headcount": r["headcount"],
            }
            for r in rows
        ]
        return {"status": "success", "departments": departments}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_department_details(department_id: int) -> Dict[str, Any]:
    """
    Get full details for a department including its head, employee list, and budget.

    Args:
        department_id: The ID of the department to retrieve.
    """
    try:
        conn = _get_connection()

        dept = conn.execute(
            "SELECT * FROM departments WHERE id = ?", (department_id,)
        ).fetchone()
        if not dept:
            conn.close()
            return {"status": "error", "error_message": f"Department with id {department_id} not found"}

        head = None
        if dept["head_employee_id"]:
            head_row = conn.execute(
                "SELECT id, first_name, last_name, title, email FROM employees WHERE id = ?",
                (dept["head_employee_id"],),
            ).fetchone()
            if head_row:
                head = dict(head_row)

        employees = [
            dict(r)
            for r in conn.execute(
                "SELECT id, first_name, last_name, title, email, status, hire_date, salary "
                "FROM employees WHERE department_id = ? ORDER BY id",
                (department_id,),
            ).fetchall()
        ]
        conn.close()

        return {
            "status": "success",
            "department": {
                "id": dept["id"],
                "name": dept["name"],
                "location": dept["location"],
                "budget": dept["budget"],
                "head": head,
                "employees": employees,
                "total_employees": len(employees),
            },
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def list_employees(
    department_id: Optional[int] = None,
    status: Optional[Literal["active", "on_leave", "inactive"]] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search and filter employees by department, status, or title (substring match).

    Args:
        department_id: Filter by department ID.
        status: Filter by employee status: active, on_leave, or inactive.
        title: Filter by job title (case-insensitive substring match).
    """
    try:
        conn = _get_connection()
        query = (
            "SELECT e.*, d.name AS department_name "
            "FROM employees e "
            "LEFT JOIN departments d ON d.id = e.department_id "
            "WHERE 1=1"
        )
        params: list = []

        if department_id is not None:
            query += " AND e.department_id = ?"
            params.append(department_id)
        if status is not None:
            query += " AND e.status = ?"
            params.append(status)
        if title is not None:
            query += " AND e.title LIKE ?"
            params.append(f"%{title}%")

        query += " ORDER BY e.id"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        employees = [dict(r) for r in rows]
        return {"status": "success", "employees": employees, "total": len(employees)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_employee_details(employee_id: int) -> Dict[str, Any]:
    """
    Get full details for a single employee including department name and manager name.

    Args:
        employee_id: The ID of the employee to retrieve.
    """
    try:
        conn = _get_connection()
        row = conn.execute(
            """
            SELECT e.*,
                   d.name AS department_name,
                   m.first_name || ' ' || m.last_name AS manager_name
            FROM employees e
            LEFT JOIN departments d ON d.id = e.department_id
            LEFT JOIN employees m  ON m.id = e.manager_id
            WHERE e.id = ?
            """,
            (employee_id,),
        ).fetchone()
        conn.close()

        if not row:
            return {"status": "error", "error_message": f"Employee with id {employee_id} not found"}

        return {"status": "success", "employee": dict(row)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_org_chart(department_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Get a hierarchical view of the organisation showing manager -> direct reports.
    Optionally filter by department.

    Args:
        department_id: If provided, restrict the chart to this department.
    """
    try:
        conn = _get_connection()
        query = (
            "SELECT e.id, e.first_name, e.last_name, e.title, e.manager_id, "
            "e.department_id, d.name AS department_name, e.status "
            "FROM employees e "
            "LEFT JOIN departments d ON d.id = e.department_id"
        )
        params: list = []
        if department_id is not None:
            query += " WHERE e.department_id = ?"
            params.append(department_id)
        query += " ORDER BY e.id"

        rows = conn.execute(query, params).fetchall()
        conn.close()

        # Build lookup
        emp_map: Dict[int, dict] = {}
        for r in rows:
            emp_map[r["id"]] = {
                "id": r["id"],
                "name": f"{r['first_name']} {r['last_name']}",
                "title": r["title"],
                "department": r["department_name"],
                "status": r["status"],
                "direct_reports": [],
            }

        # Populate direct_reports
        roots = []
        for r in rows:
            eid = r["id"]
            mid = r["manager_id"]
            if mid and mid in emp_map:
                emp_map[mid]["direct_reports"].append(emp_map[eid])
            else:
                roots.append(emp_map[eid])

        return {"status": "success", "org_chart": roots}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_direct_reports(manager_id: int) -> Dict[str, Any]:
    """
    List employees who directly report to a given manager.

    Args:
        manager_id: The employee ID of the manager.
    """
    try:
        conn = _get_connection()

        manager = conn.execute(
            "SELECT id, first_name, last_name, title FROM employees WHERE id = ?",
            (manager_id,),
        ).fetchone()
        if not manager:
            conn.close()
            return {"status": "error", "error_message": f"Manager with id {manager_id} not found"}

        reports = [
            dict(r)
            for r in conn.execute(
                "SELECT id, first_name, last_name, title, email, status, hire_date, salary "
                "FROM employees WHERE manager_id = ? ORDER BY id",
                (manager_id,),
            ).fetchall()
        ]
        conn.close()

        return {
            "status": "success",
            "manager": dict(manager),
            "direct_reports": reports,
            "total": len(reports),
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def list_leave_requests(
    employee_id: Optional[int] = None,
    status: Optional[Literal["pending", "approved", "rejected"]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List and filter leave requests.

    Args:
        employee_id: Filter by employee ID.
        status: Filter by request status: pending, approved, or rejected.
        date_from: Only include requests whose start_date is on or after this date (YYYY-MM-DD).
        date_to: Only include requests whose end_date is on or before this date (YYYY-MM-DD).
    """
    try:
        conn = _get_connection()
        query = (
            "SELECT lr.*, "
            "e.first_name || ' ' || e.last_name AS employee_name, "
            "a.first_name || ' ' || a.last_name AS approver_name "
            "FROM leave_requests lr "
            "JOIN employees e ON e.id = lr.employee_id "
            "LEFT JOIN employees a ON a.id = lr.approved_by "
            "WHERE 1=1"
        )
        params: list = []

        if employee_id is not None:
            query += " AND lr.employee_id = ?"
            params.append(employee_id)
        if status is not None:
            query += " AND lr.status = ?"
            params.append(status)
        if date_from is not None:
            query += " AND lr.start_date >= ?"
            params.append(date_from)
        if date_to is not None:
            query += " AND lr.end_date <= ?"
            params.append(date_to)

        query += " ORDER BY lr.start_date DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        return {
            "status": "success",
            "leave_requests": [dict(r) for r in rows],
            "total": len(rows),
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def submit_leave_request(
    employee_id: int,
    leave_type: Literal["vacation", "sick", "personal", "parental"],
    start_date: str,
    end_date: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submit a new leave request for an employee.  Validates that the employee
    exists, is active, and that start_date is before end_date.

    Args:
        employee_id: The ID of the employee requesting leave.
        leave_type: Type of leave: vacation, sick, personal, or parental.
        start_date: Start date of the leave (YYYY-MM-DD).
        end_date: End date of the leave (YYYY-MM-DD).
        reason: Optional reason for the leave request.
    """
    try:
        # Validate dates
        if start_date >= end_date:
            return {
                "status": "error",
                "error_message": "start_date must be before end_date",
            }

        conn = _get_connection()

        emp = conn.execute(
            "SELECT id, first_name, last_name, status FROM employees WHERE id = ?",
            (employee_id,),
        ).fetchone()
        if not emp:
            conn.close()
            return {"status": "error", "error_message": f"Employee with id {employee_id} not found"}
        if emp["status"] != "active":
            conn.close()
            return {
                "status": "error",
                "error_message": f"Employee {emp['first_name']} {emp['last_name']} is not active (current status: {emp['status']}). Only active employees can submit leave requests.",
            }

        cur = conn.execute(
            "INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, status, reason) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (employee_id, leave_type, start_date, end_date, reason),
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "leave_request": {
                "id": new_id,
                "employee_id": employee_id,
                "employee_name": f"{emp['first_name']} {emp['last_name']}",
                "leave_type": leave_type,
                "start_date": start_date,
                "end_date": end_date,
                "status": "pending",
                "reason": reason,
            },
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_performance_reviews(
    employee_id: int,
    review_period: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get performance reviews for an employee, optionally filtered by review period.

    Args:
        employee_id: The ID of the employee whose reviews to retrieve.
        review_period: Optional filter such as '2024-H1' or '2024-H2'.
    """
    try:
        conn = _get_connection()

        emp = conn.execute(
            "SELECT id, first_name, last_name FROM employees WHERE id = ?",
            (employee_id,),
        ).fetchone()
        if not emp:
            conn.close()
            return {"status": "error", "error_message": f"Employee with id {employee_id} not found"}

        query = (
            "SELECT pr.*, "
            "r.first_name || ' ' || r.last_name AS reviewer_name "
            "FROM performance_reviews pr "
            "JOIN employees r ON r.id = pr.reviewer_id "
            "WHERE pr.employee_id = ?"
        )
        params: list = [employee_id]

        if review_period is not None:
            query += " AND pr.review_period = ?"
            params.append(review_period)

        query += " ORDER BY pr.review_date DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()

        return {
            "status": "success",
            "employee": {
                "id": emp["id"],
                "name": f"{emp['first_name']} {emp['last_name']}",
            },
            "reviews": [dict(r) for r in rows],
            "total": len(rows),
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_department_headcount_summary() -> Dict[str, Any]:
    """
    Get an aggregate summary per department: active count, on-leave count, inactive count, and average salary.
    """
    try:
        conn = _get_connection()
        rows = conn.execute("""
            SELECT
                d.name                                                         AS department_name,
                COUNT(CASE WHEN e.status = 'active'   THEN 1 END)             AS active_count,
                COUNT(CASE WHEN e.status = 'on_leave'  THEN 1 END)            AS on_leave_count,
                COUNT(CASE WHEN e.status = 'inactive'  THEN 1 END)            AS inactive_count,
                ROUND(AVG(e.salary), 2)                                        AS avg_salary
            FROM departments d
            LEFT JOIN employees e ON e.department_id = d.id
            GROUP BY d.id
            ORDER BY d.id
        """).fetchall()
        conn.close()

        return {
            "status": "success",
            "summary": [dict(r) for r in rows],
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
