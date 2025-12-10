from flask import Flask, render_template, request, redirect
from neo4j import GraphDatabase

app = Flask(__name__)

# ======================================================
# 🔹 1. NEO4J CONNECTION
# ======================================================
URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "Tlohitha@123"   # change this to your real Neo4j password

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


# Helper to run queries
def run_query(query, parameters=None):
    if parameters is None:
        parameters = {}
    with driver.session() as session:
        return session.run(query, parameters)


# ======================================================
# 🔹 2. HOME REDIRECT
# ======================================================
@app.route("/")
def home():
    return redirect("/create")


# ======================================================
# 🔹 3. CREATE USER — SHOW FORM
# ======================================================
@app.route("/create", methods=["GET"])
def create_form():
    return render_template("create_user.html")


# ======================================================
# 🔹 4. CREATE USER — INSERT INTO NEO4J
# ======================================================
@app.route("/create", methods=["POST"])
def create_user():
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    email = request.form["email"]
    mobile = request.form["mobile"]

    query = """
        CREATE (u:User {
            firstname: $firstname,
            lastname: $lastname,
            email: $email,
            mobile: $mobile
        })
    """

    run_query(query, {
        "firstname": firstname,
        "lastname": lastname,
        "email": email,
        "mobile": mobile
    })

    return redirect("/users")


# ======================================================
# 🔹 5. READ USERS — SHOW ALL USERS
# ======================================================
@app.route("/users")
def list_users():
    query = "MATCH (u:User) RETURN u"
    result = run_query(query)

    users = []
    for record in result:
        node = record["u"]
        users.append({
            "firstname": node["firstname"],
            "lastname": node["lastname"],
            "email": node["email"],
            "mobile": node["mobile"]
        })

    return render_template("users.html", users=users)


# ======================================================
# 🔹 6. EDIT USER — LOAD EXISTING DATA
# ======================================================
@app.route("/edit/<email>")
def edit_user(email):
    query = "MATCH (u:User {email:$email}) RETURN u"
    result = run_query(query, {"email": email}).single()

    if result:
        u = result["u"]
        user = {
            "firstname": u["firstname"],
            "lastname": u["lastname"],
            "email": u["email"],
            "mobile": u["mobile"]
        }
        return render_template("edit_user.html", user=user)

    return "User not found"


# ======================================================
# 🔹 7. UPDATE USER — SAVE CHANGES
# ======================================================
@app.route("/update/<email>", methods=["POST"])
def update_user(email):
    firstname = request.form["firstname"]
    lastname = request.form["lastname"]
    mobile = request.form["mobile"]

    query = """
        MATCH (u:User {email:$email})
        SET u.firstname = $firstname,
            u.lastname = $lastname,
            u.mobile = $mobile
    """

    run_query(query, {
        "firstname": firstname,
        "lastname": lastname,
        "mobile": mobile,
        "email": email
    })

    return redirect("/users")


# ======================================================
# 🔹 8. DELETE USER
# ======================================================
@app.route("/delete/<email>")
def delete_user(email):
    query = "MATCH (u:User {email:$email}) DETACH DELETE u"
    run_query(query, {"email": email})
    return redirect("/users")


# ======================================================
# 🔹 RUN FLASK
# ======================================================
if __name__ == "__main__":
    app.run(debug=True)
