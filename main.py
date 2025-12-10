from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from neo4j import GraphDatabase
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Neo4j Connection
uri = "neo4j://127.0.0.1:7687"
username = "neo4j"
password = "Tlohitha@123"   # replace with your Neo4j password
driver = GraphDatabase.driver(uri, auth=(username, password))

# User Model
class User(BaseModel):
    firstname: str
    lastname: str
    email: str
    mobile: str

# =========================
# Existing Users Page
# =========================
# @app.get("/existing_users", response_class=HTMLResponse)
# def existing_users(request: Request):
#     query = "MATCH (u:User) RETURN u"
#     users_list = []
#     with driver.session() as session:
#         result = session.run(query)
#         for record in result:
#             node = record["u"]
#             users_list.append({
#                 "firstname": node.get("firstname") or "",
#                 "lastname": node.get("lastname") or "",
#                 "fullname": f"{node.get('firstname') or ''} {node.get('lastname') or ''}".strip(),
#                 "email": node.get("email") or "",
#                 "mobile": node.get("mobile") or ""
#             })
#     return templates.TemplateResponse("Existing_user.html", {"request": request, "users": users_list})
@app.get("/existing_users", response_class=HTMLResponse)
def existing_users(request: Request):
    query = "MATCH (u:User) RETURN u ORDER BY u.created_at DESC"
    users_list = []

    with driver.session() as session:
        result = session.run(query)
        for record in result:
            node = record["u"]
            users_list.append({
                "firstname": node.get("firstname") or "",
                "lastname": node.get("lastname") or "",
                "fullname": f"{node.get('firstname')} {node.get('lastname')}",
                "email": node.get("email"),
                "mobile": node.get("mobile")
            })

    return templates.TemplateResponse("Existing_user.html", {
        "request": request,
        "users": users_list
    })

# =========================
# Add User Form
# =========================
@app.get("/create_user", response_class=HTMLResponse)
def create_user_form(request: Request):
    return templates.TemplateResponse(
        "create_userform.html",
        {
            "request": request,
            "title": "Create New User",
            "action_url": "/create_user",
            "button_text": "Save User",
            "user": None
        }
    )
#-================Post ================
# @app.post("/create_user")
# def create_user(
#     firstname: str = Form(...),
#     lastname: str = Form(...),
#     email: str = Form(...),
#     mobile: str = Form(...)
# ):
#     fullname = f"{firstname} {lastname}"
#     query = """
#     CREATE (u:User {firstname: $firstname, lastname: $lastname, fullname: $fullname, email: $email, mobile: $mobile})
#     """
#     with driver.session() as session:
#         session.run(query, {
#             "firstname": firstname,
#             "lastname": lastname,
#             "fullname": fullname,
#             "email": email,
#             "mobile": mobile
#         })
#     return RedirectResponse(url="/existing_users", status_code=303)
@app.post("/create_user")
def create_user(
    firstname: str = Form(...),
    lastname: str = Form(...),
    email: str = Form(...),
    mobile: str = Form(...)
):
    # --------------------------
    # VALIDATION: Mobile must be 10 digits
    # --------------------------
    if not mobile.isdigit() or len(mobile) != 10:
        return HTMLResponse(
            "<h3 style='color:red;'>Mobile number must be exactly 10 digits.</h3>"
            "<a href='/create_user'>Go Back</a>"
        )

    with driver.session() as session:

        # --------------------------
        # VALIDATION: Duplicate Email
        # --------------------------
        email_query = "MATCH (u:User {email: $email}) RETURN u"
        if session.run(email_query, {"email": email}).single():
            return HTMLResponse(
                "<h3 style='color:red;'>Email already exists. Enter another email.</h3>"
                "<a href='/create_user'>Go Back</a>"
            )

        # --------------------------
        # VALIDATION: Duplicate Mobile
        # --------------------------
        mobile_query = "MATCH (u:User {mobile: $mobile}) RETURN u"
        if session.run(mobile_query, {"mobile": mobile}).single():
            return HTMLResponse(
                "<h3 style='color:red;'>Mobile number already exists. Use another mobile.</h3>"
                "<a href='/create_user'>Go Back</a>"
            )

        # --------------------------
        # INSERT USER
        # --------------------------
        fullname = f"{firstname} {lastname}"
        query = """
        CREATE (u:User {
            firstname: $firstname,
            lastname: $lastname,
            fullname: $fullname,
            email: $email,
            mobile: $mobile,
            created_at: datetime()
        })
        """
        session.run(query, {
            "firstname": firstname,
            "lastname": lastname,
            "fullname": fullname,
            "email": email,
            "mobile": mobile
        })

    return RedirectResponse(url="/existing_users", status_code=303)

# =========================
# Edit User Form
# =========================
@app.get("/edit/{email}", response_class=HTMLResponse)
def edit_user_form(request: Request, email: str):
    query = "MATCH (u:User {email: $email}) RETURN u"
    with driver.session() as session:
        result = session.run(query, {"email": email})
        record = result.single()
        if not record:
            return HTMLResponse(f"<h3>User with email {email} not found</h3>")
        node = record["u"]
        user_data = {
            "firstname": node.get("firstname") or "",
            "lastname": node.get("lastname") or "",
            "email": node.get("email") or "",
            "mobile": node.get("mobile") or ""
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
#=====================edit email=================
@app.post("/edit/{email}")
def update_user(
    email: str,
    firstname: str = Form(...),
    lastname: str = Form(...),
    mobile: str = Form(...)
):
    # ---- Mobile validation ----
    if not mobile.isdigit() or len(mobile) != 10:
        return HTMLResponse(
            "<h3 style='color:red;'>Mobile number must be exactly 10 digits.</h3>"
            "<a href='/edit/{email}'>Go Back</a>"
        )

    with driver.session() as session:

        # ---- Check duplicate mobile (except same user) ----
        duplicate_query = """
        MATCH (u:User)
        WHERE u.mobile = $mobile AND u.email <> $email
        RETURN u
        """

        if session.run(duplicate_query, {"mobile": mobile, "email": email}).single():
            return HTMLResponse(
                "<h3 style='color:red;'>Mobile number already used by another user.</h3>"
                "<a href='/edit/{email}'>Go Back</a>"
            )

        # ---- UPDATE USER ----
        fullname = f"{firstname} {lastname}"
        query = """
        MATCH (u:User {email: $email})
        SET u.firstname = $firstname,
            u.lastname = $lastname,
            u.fullname = $fullname,
            u.mobile = $mobile
        """

        session.run(query, {
            "email": email,
            "firstname": firstname,
            "lastname": lastname,
            "fullname": fullname,
            "mobile": mobile
        })

    return RedirectResponse(url="/existing_users", status_code=303)

# =========================
# Delete User
# =========================
@app.get("/delete/{email}")
def delete_user(email: str):
    query = "MATCH (u:User {email: $email}) DETACH DELETE u"
    with driver.session() as session:
        session.run(query, {"email": email})
    return RedirectResponse(url="/existing_users", status_code=303)

# from fastapi import FastAPI, Request
# from pydantic import BaseModel
# from neo4j import GraphDatabase
# from fastapi.templating import Jinja2Templates
# from fastapi.responses import HTMLResponse
# from fastapi.responses import RedirectResponse

# app = FastAPI()
# templates = Jinja2Templates(directory="templates")

# # Neo4j Connection
# uri = "neo4j://127.0.0.1:7687"
# username = "neo4j"
# password = "Tlohitha@123"   # replace with your Neo4j password
# driver = GraphDatabase.driver(uri, auth=(username, password))

# # User Model
# class User(BaseModel):
#     firstname: str
#     lastname: str
#     email: str
#     mobile: str

# # Create User API
# @app.post("/create_user")
# def create_user(user: User):
#     try:
#         query = """
#         CREATE (u:User {
#             firstname: $firstname,
#             lastname: $lastname,
#             email: $email,
#             mobile: $mobile
#         })
#         RETURN u
#         """
#         with driver.session() as session:
#             session.run(query, {
#                 "firstname": user.firstname,
#                 "lastname": user.lastname,
#                 "email": user.email,
#                 "mobile": user.mobile
#             })
#         return {"message": "User created successfully"}
#     except Exception as e:
#         return {"error": str(e)}

# # Fetch All Users API
# @app.get("/users")
# def get_users():
#     query = """
#     MATCH (u:User)
#     WHERE u.firstname IS NOT NULL AND u.firstname <> ""
#       AND u.lastname IS NOT NULL AND u.lastname <> ""
#     RETURN u
#     """

#     users_list = []
#     with driver.session() as session:
#         result = session.run(query)
#         for record in result:
#             node = record["u"]
#             users_list.append({
#                 "firstname": node.get("firstname") or "",
#                 "lastname": node.get("lastname") or "",
#                 "fullname": f"{node.get('firstname') or ''} {node.get('lastname') or ''}".strip(),
#                 "email": node.get("email") or "",
#                 "mobile": node.get("mobile") or ""
#             })

#     return {"users": users_list}

# @app.get("/create_userform", response_class=HTMLResponse)
# def create_user_form_alias(request: Request):
#     return templates.TemplateResponse("create_userform.html", {"request": request})
# from fastapi import Request
# from fastapi.responses import HTMLResponse

# # @app.get("/existing_user", response_class=HTMLResponse)
# # def existing_users_page(request: Request):
# #     # Fetch users from Neo4j
# #     query = """
# #     MATCH (u:User)
# #     WHERE u.firstname IS NOT NULL AND u.firstname <> ""
# #       AND u.lastname IS NOT NULL AND u.lastname <> ""
# #     RETURN u
# #     """
# #     users_list = []
# #     with driver.session() as session:
# #         result = session.run(query)
# #         for record in result:
# #             node = record["u"]
# #             users_list.append({
# #                 "firstname": node.get("firstname") or "",
# #                 "lastname": node.get("lastname") or "",
# #                 "email": node.get("email") or "",
# #                 "mobile": node.get("mobile") or ""
# #             })

# #     # Use your actual file name here (case-sensitive)
# #     return templates.TemplateResponse("Existing_user.html", {
# #         "request": request,
# #         "users": users_list
# #     })
# @app.get("/existing_users", response_class=HTMLResponse)
# def existing_users(request: Request):
#     query = "MATCH (u:User) RETURN u"
#     users_list = []
#     with driver.session() as session:
#         result = session.run(query)
#         for record in result:
#             node = record["u"]
#             users_list.append({
#                 "firstname": node.get("firstname") or "",
#                 "lastname": node.get("lastname") or "",
#                 "fullname": f"{node.get('firstname') or ''} {node.get('lastname') or ''}".strip(),
#                 "email": node.get("email") or "",
#                 "mobile": node.get("mobile") or ""
#             })

#     # Match the exact filename
#     return templates.TemplateResponse("Existing_user.html", {
#         "request": request,
#         "users": users_list
#     })

# @app.get("/edit/{email}", response_class=HTMLResponse)
# def edit_user_form(request: Request, email: str):
#     query = "MATCH (u:User {email: $email}) RETURN u"
#     with driver.session() as session:
#         result = session.run(query, {"email": email})
#         record = result.single()
#         if not record:
#             return HTMLResponse(f"<h3>User with email {email} not found</h3>")
#         node = record["u"]
#         user_data = {
#             "firstname": node.get("firstname") or "",
#             "lastname": node.get("lastname") or "",
#             "email": node.get("email") or "",
#             "mobile": node.get("mobile") or ""
#         }
#     return templates.TemplateResponse("edit_user.html", {
#         "request": request,
#         "user": user_data
#     })
# from fastapi import Form
# from fastapi.responses import RedirectResponse

# @app.post("/edit/{email}")
# def update_user(
#     email: str,
#     firstname: str = Form(...),
#     lastname: str = Form(...),
#     mobile: str = Form(...)
# ):
#     query = """
#     MATCH (u:User {email: $email})
#     SET u.firstname = $firstname,
#         u.lastname = $lastname,
#         u.mobile = $mobile
#     RETURN u
#     """
#     with driver.session() as session:
#         session.run(query, {"email": email, "firstname": firstname, "lastname": lastname, "mobile": mobile})
    
#     # Redirect to Existing Users page after update
#     return RedirectResponse(url="/existing_users", status_code=303)
# @app.get("/delete/{email}")
# def delete_user(email: str):
#     query = """
#     MATCH (u:User {email: $email})
#     DETACH DELETE u
#     """

#     with driver.session() as session:
#         session.run(query, {"email": email})

#     # Redirect back to existing users page
#     return RedirectResponse(url="/existing_users", status_code=303)