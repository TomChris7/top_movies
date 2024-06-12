from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests



URL = "https://api.themoviedb.org/3/search/movie"
URL_2 = "https://api.themoviedb.org/3/movie/{movie_id}"
IMAGES_URL = "https://image.tmdb.org/t/p/w500"
# api_token = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlNWQxMGZlMTRmMDAzNmU2ODBhODFlZGU1ZTM3ZDJmYyIsInN1YiI6IjY2NjI0Mzg4MzkxNTFjNTUyM2YyMmQ5NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.4VyMX7xak3I83SnkDe7Nw0hndf-3oIhQCTbPQ8cfuHE"
api_token = "e5d10fe14f0036e680a81ede5e37d2fc"


headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlNWQxMGZlMTRmMDAzNmU2ODBhODFlZGU1ZTM3ZDJmYyIsInN1YiI6IjY2NjI0Mzg4MzkxNTFjNTUyM2YyMmQ5NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.4VyMX7xak3I83SnkDe7Nw0hndf-3oIhQCTbPQ8cfuHE",

}


app = Flask(__name__)
# app.secret_key = "top10moviesmylist"
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top_movies.db"
db.init_app(app)


# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


# Create WTF Forms
class NewMovie(FlaskForm):
    movie_title = StringField("Enter Movie Title", validators=[DataRequired()])
    search = SubmitField("Search")


class EditForm(FlaskForm):
    movie_review = StringField(label="Your Review", validators=[DataRequired()])
    movie_rating = StringField(label="Your Rating Out of 10 e.g. 6.5", validators=[DataRequired()])
    submit = SubmitField("Update")


# # Adding a movie to the database manuelly
# new_movie = Movie(
#     title="Avatar The Way of 2022",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     # rating=7.3,
#     # ranking=9,
#     # review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
#
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()


# Creating URL routes and their page data and function
@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()
    for movie in all_movies:
        movie.ranking = (all_movies.index(movie)+1)
        db.session.commit()
    return render_template("index.html", movies=all_movies)



@app.route("/edit", methods=["GET", "POST"])
def edit():
    movie_update = EditForm()
    movie_id = request.args.get("movie_id")
    result = db.get_or_404(Movie, movie_id)
    if movie_update.validate_on_submit():
        result.rating = movie_update.movie_rating.data
        result.review = movie_update.movie_review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=movie_update, movie=result)


@app.route("/delete")
def delete():
    movie_id = request.args.get("movie_id")
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    movie_search = NewMovie()
    if movie_search.validate_on_submit():
        return redirect(url_for("select", name=movie_search.movie_title.data))
    return render_template("add.html", form=movie_search)


@app.route("/select", methods=["GET", "POST"])
def select():
    user_title = request.args.get("name")
    # print(user_title)
    params = {
        "query": f"{user_title}"
    }
    response = requests.get(URL, headers=headers, params=params)
    movie_response = response.json()
    movie_results = movie_response["total_results"]
    movie_list = movie_response["results"]

    return render_template("select.html", results=movie_results, movies=movie_list)

@app.route("/find")
def find():
    selected_movie = request.args.get("id")
    print(selected_movie)
    if selected_movie:
        response_2 = requests.get(URL_2.format(movie_id=selected_movie), headers=headers)
        movie_response_2 = response_2.json()
        # print(movie_response_2)
        new_movies = Movie(
            title=movie_response_2["title"],
            img_url=f"{IMAGES_URL.format(movie_id=selected_movie)}{movie_response_2['poster_path']}",
            year=movie_response_2["release_date"].split("-")[0],
            description=movie_response_2["overview"]
        )
        db.session.add(new_movies)
        db.session.commit()
        return redirect(url_for("edit", movie_id=new_movies.id))


if __name__ == '__main__':
    app.run(debug=True)
