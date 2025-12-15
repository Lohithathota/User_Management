from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from neo4j import GraphDatabase

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =========================
# Neo4j Connection
# =========================
driver = GraphDatabase.driver(
    "neo4j://127.0.0.1:7687",
    auth=("neo4j", "Tlohitha@123")
)

# =========================
# Pydantic Model (JSON API)
# =========================
class UserCreate(BaseModel):
    firstname: str
    lastname: str
    email: EmailStr
    mobile: str = Field(..., pattern="^[0-9]{10}$")

# =========================
# EXISTING USERS (HTML)
# =========================
@app.get("/existing_users", response_class=HTMLResponse)
def existing_users(request: Request):
    query = "MATCH (u:User) RETURN u ORDER BY u.created_at DESC"
    users = []

    with driver.session() as session:
        result = session.run(query)
        for record in result:
            u = record["u"]
            users.append({
                "firstname": u.get("firstname"),
                "lastname": u.get("lastname"),
                "fullname": f"{u.get('firstname')} {u.get('lastname')}",
                "email": u.get("email"),
                "mobile": u.get("mobile")
            })

    return templates.TemplateResponse(
        "Existing_user.html",
        {"request": request, "users": users}
    )
# =========================
# CREATE USER FORM (HTML)
# =========================
@app.get("/create_user", response_class=HTMLResponse)
def create_user_form(request: Request):
    return templates.TemplateResponse(
        "create_userform.html",
        {
            "request": request,
            "title": "Create User",
            "action_url": "/create_user",
            "button_text": "Save User",
            "user": None
        }
    )

# =========================
# CREATE USER (HTML FORM SUBMIT)
# =========================
@app.post("/create_user")
def create_user_form_submit(
    firstname: str = Form(...),
    lastname: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...)
):
    if not mobile.isdigit() or len(mobile) != 10:
        return HTMLResponse("<h3>Invalid mobile number</h3>")

    with driver.session() as session:
        if session.run("MATCH (u:User {email:$email}) RETURN u", {"email": email}).single():
            return HTMLResponse("<h3>Email already exists</h3>")

        fullname = f"{firstname} {lastname}"

        session.run(
            """
            CREATE (u:User {
                firstname:$firstname,
                lastname:$lastname,
                fullname:$fullname,
                email:$email,
                mobile:$mobile,
                created_at: datetime()
            })
            """,
            {
                "firstname": firstname,
                "lastname": lastname,
                "fullname": fullname,
                "email": email,
                "mobile": mobile
            }
        )

    return RedirectResponse(url="/existing_users", status_code=303)

# =========================
# EDIT USER FORM (HTML)
# =========================
@app.get("/edit/{email}", response_class=HTMLResponse)
def edit_user_form(request: Request, email: str):
    with driver.session() as session:
        record = session.run(
            "MATCH (u:User {email:$email}) RETURN u",
            {"email": email}
        ).single()

        if not record:
            return HTMLResponse("<h3>User not found</h3>")

        u = record["u"]
        user_data = {
            "firstname": u.get("firstname"),
            "lastname": u.get("lastname"),
            "email": u.get("email"),
            "mobile": u.get("mobile")
        }

    return templates.TemplateResponse(
        "create_userform.html",
        {
            "request": request,
            "title": "Edit User",
            "action_url": f"/edit/{email}",
            "button_text": "Update User",
            "user": user_data
        }
    )

# =========================
# UPDATE USER (HTML FORM)
# =========================
@app.post("/edit/{email}")
def update_user(
    email: str,
    firstname: str = Form(...),
    lastname: str = Form(...),
    mobile: str = Form(...)
):
    if not mobile.isdigit() or len(mobile) != 10:
        return HTMLResponse("<h3>Invalid mobile number</h3>")

    with driver.session() as session:
        fullname = f"{firstname} {lastname}"
        session.run(
            """
            MATCH (u:User {email:$email})
            SET u.firstname=$firstname,
                u.lastname=$lastname,
                u.fullname=$fullname,
                u.mobile=$mobile
            """,
            {
                "email": email,
                "firstname": firstname,
                "lastname": lastname,
                "fullname": fullname,
                "mobile": mobile
            }
        )

    return RedirectResponse(url="/existing_users", status_code=303)

# =========================
# DELETE USER
# =========================
@app.get("/delete/{email}")
def delete_user(email: str):
    with driver.session() as session:
        session.run(
            "MATCH (u:User {email:$email}) DETACH DELETE u",
            {"email": email}
        )

    return RedirectResponse(url="/existing_users", status_code=303)
