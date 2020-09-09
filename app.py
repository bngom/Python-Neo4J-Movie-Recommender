from models import User, get_page_items, get_pagination, get_movies
from flask import Flask, request, session, redirect, url_for, render_template, flash


app = Flask(__name__)
app.secret_key = "super secret key"


@app.route("/")
def main():
    """This is the entry point of the application
    :return
        Render the main page of the website: A list of US movies from 90"s and option to log in or register
    """
    page, per_page, offset = get_page_items()
    movies, total = get_movies(offset, per_page)

    pagination = get_pagination(page=page,
                                per_page=per_page,  # results per page
                                total=total,  # total number of results
                                format_total=True,  # format total. example 1,024
                                format_number=True,  # turn on format flag
                                record_name="movies",  # provide context
                                )
    return render_template("index.html",
                           movies=movies,
                           page=page,
                           total=total,
                           per_page=per_page,
                           pagination=pagination
                           )


@app.route("/showSignUp", methods=["GET","POST"])
def showSignUp():
    """Show the sign up form and implement some business logics.
    - Verify length of login and password
    - check if the username chosen aready exist"""
    if request.method == "POST":
        username = request.form["inputName"]
        password = request.form["inputPassword"]

        if len(username) < 1:
            flash("Please type in a login")
        elif len(password) < 5:
            flash("Password must have at least 5 characters")
        elif not User(username).register(password):
            flash("A user with that username already exists.")
        else:
            session["username"] = username
            flash("Logged in.")
            return redirect(url_for("main"))

    return render_template("register.html")

@app.route("/showSignIn", methods=["GET", "POST"])
def showSignIn():
    if request.method == "POST":
        username = request.form["inputName"]
        password = request.form["inputPassword"]
        #print(username+" "+password)
        if not User(username).verify_password(password):
            flash("Invalid username or password.")
        else:
            session["username"] = username
            flash("Logged in.")
            return redirect(url_for("main"))

    return render_template("login.html")


@app.route("/engine")
def recommenderEngine():
    """Based on movies category liked by the connected user a recommendation is generated"""
    # get the session username
    username=session.get("username")
    # get a list of movie recommended for the connected user
    movies = User(username).get_recommendation()
    # rendering
    return render_template("recommendedMovies.html", username=username, movies=movies)

@app.route("/logout")
def logout():
    """Log out the connected user"""
    session.pop("username", None)
    flash("Logged out.")
    return redirect(url_for("main"))


@app.route("/like_movie/<movieId>")
def like_movie(movieId):
    """Allow the connected user to like a movie.
     This action generate a relation in Neo4j
      between the User and the movie:
            (user)-[:LIKED]-(movie)
    :argument
        - movieId: The id of the movie liked by the used """
    username = session.get("username")
    # Only logged in user are authorised to like a movie
    if not username:
        flash("You must be logged in to like a movie.")
        return redirect(url_for("login"))

    User(username).like_movie(movieId)

    flash("Liked movie.")
    return redirect(request.referrer)

@app.route("/profile/<username>")
def profile(username):
    logged_in_username = session.get("username")
    user_being_viewed_username = username

    user_being_viewed = User(user_being_viewed_username)
    movies = user_being_viewed.get_recommanded_movies()

    return render_template(
        "profile.html",
        username=username,
        posts=movies
    )


if __name__ == "__main__":
    app.run()
