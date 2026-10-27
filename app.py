from __future__ import annotations

import html
import inspect
from pathlib import Path
from urllib.parse import quote

import gradio as gr
import numpy as np
import pandas as pd
from fastapi import FastAPI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "u.item"
THEATER_IMAGE_PATH = BASE_DIR / "Untitled design (1).jpg"
POSTER_IMAGE_PATH = BASE_DIR / "image_f0140cfc.jpg"
GENRE_NAMES = [
    "unknown",
    "Action",
    "Adventure",
    "Animation",
    "Childrens",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western",
]
DATASET_COLUMNS = [
    "movie_id",
    "title",
    "release_date",
    "video_release_date",
    "imdb_url",
    *GENRE_NAMES,
    "imdb_rating",
    "imdb_votes",
    "industry",
    "is_synthetic",
    "profile",
]
MOVIE_MODE = "By Movie Title (Seen Before)"
GENRE_MODE = "By Genre & Category Filter Combo"
BLOCKS_ACCEPTS_CSS = "css" in inspect.signature(gr.Blocks).parameters
LAUNCH_ACCEPTS_CSS = "css" in inspect.signature(gr.Blocks.launch).parameters

BACKGROUND_IMAGE_PATHS = [
    image_path
    for image_path in (THEATER_IMAGE_PATH, POSTER_IMAGE_PATH)
    if image_path.is_file()
]
BACKGROUND_IMAGE_URLS = [
    "/gradio_api/file=" + quote(image_path.as_posix(), safe="/:")
    for image_path in BACKGROUND_IMAGE_PATHS
]
if BACKGROUND_IMAGE_PATHS:
    gr.set_static_paths(paths=BACKGROUND_IMAGE_PATHS)

THEATER_IMAGE_LAYER = (
    f', url("{BACKGROUND_IMAGE_URLS[0]}")'
    if THEATER_IMAGE_PATH.is_file()
    else ""
)
POSTER_IMAGE_LAYER = (
    f'url("{BACKGROUND_IMAGE_URLS[-1]}")'
    if POSTER_IMAGE_PATH.is_file()
    else ""
)
NETFLIX_THEME_CSS = f"""
html, body {{
    min-height: 100%;
    background-color: #0f0b19 !important;
    background-image:
        linear-gradient(rgba(15, 11, 25, 0.85), rgba(15, 11, 25, 0.96)){THEATER_IMAGE_LAYER} !important;
    background-size: cover;
    background-attachment: fixed;
    background-position: center;
    background-repeat: no-repeat;
    color: #f8f5f7 !important;
    font-family: Inter, "Segoe UI", Arial, sans-serif !important;
}}

gradio-app {{
    min-height: 100vh;
    background: transparent !important;
}}

body::before {{
    content: "";
    position: fixed;
    z-index: 0;
    inset: 0;
    pointer-events: none;
    opacity: 0.3;
    background-image: {POSTER_IMAGE_LAYER or "none"};
    background-repeat: no-repeat;
    background-position: right 4vw center;
    background-size: min(48vw, 680px) auto;
    mask-image: linear-gradient(to left, black 0%, rgba(0, 0, 0, 0.75) 58%, transparent 100%);
}}

.gradio-container {{
    position: relative;
    z-index: 1;
    max-width: 1120px !important;
    margin: 30px auto !important;
    padding: clamp(18px, 4vw, 42px) !important;
    color: #f8f5f7 !important;
    background: rgba(15, 11, 25, 0.24) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 20px !important;
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.48) !important;
    backdrop-filter: blur(2px);
}}

#moodmatcher-title,
#moodmatcher-subtitle {{
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}}

#moodmatcher-title h1 {{
    margin: 0.3em 0 0.12em !important;
    color: #ff4058 !important;
    font-size: clamp(2rem, 5vw, 3.2rem) !important;
    font-weight: 850 !important;
    letter-spacing: 0.025em !important;
    text-align: center !important;
    text-shadow: 0 4px 28px rgba(229, 9, 20, 0.32);
}}

#moodmatcher-subtitle p {{
    max-width: 760px;
    margin: 0 auto 1.6rem !important;
    color: #d3cbd6 !important;
    font-size: 1rem !important;
    line-height: 1.65 !important;
    text-align: center !important;
}}

.gradio-container .form,
.gradio-container fieldset,
#recommendation-results {{
    background: rgba(27, 21, 34, 0.76) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
}}

.gradio-container .block {{
    background-color: transparent !important;
}}

.gradio-container label,
.gradio-container label span {{
    color: #f4edf2 !important;
    font-weight: 650 !important;
}}

.gradio-container input:not([type="checkbox"]):not([type="radio"]),
.gradio-container select,
.gradio-container textarea {{
    color: #fff !important;
    background: rgba(35, 28, 43, 0.96) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
}}

.gradio-container label.selected {{
    color: #fff !important;
    background: rgba(229, 9, 50, 0.24) !important;
    border-color: #ff5269 !important;
    box-shadow: 0 0 0 1px rgba(255, 64, 88, 0.25) !important;
}}

.gradio-container input[type="checkbox"]:checked {{
    background-color: #e50932 !important;
    background-image: var(--checkbox-check) !important;
    border-color: #ff5269 !important;
}}

.gradio-container input[type="radio"]:checked {{
    background-color: #e50932 !important;
    border-color: #ff5269 !important;
    box-shadow: inset 0 0 0 3px #231c2b !important;
}}

.gradio-container input[type="range"] {{
    accent-color: #e50932 !important;
}}

.gradio-container button.primary {{
    color: #fff !important;
    background: linear-gradient(135deg, #f32143, #a9062a) !important;
    border: 0 !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 26px rgba(229, 9, 50, 0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}}

.gradio-container button.primary:hover {{
    transform: translateY(-2px);
    filter: brightness(1.12);
    box-shadow: 0 12px 32px rgba(229, 9, 50, 0.42);
}}

.recommendation-list {{
    margin: 0;
    padding: 8px 0;
    list-style: none;
    background: rgba(15, 11, 25, 0.62);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
}}

.recommendation-list li {{
    padding: 14px 18px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    transition: all 0.2s ease-in-out !important;
}}

.recommendation-list li:last-child {{
    border-bottom: 0 !important;
}}

.recommendation-list li:hover {{
    padding-left: 25px !important;
    color: #ff5269 !important;
    background: rgba(107, 12, 39, 0.28) !important;
}}

#credits {{
    margin-top: 1.5rem !important;
    color: #c5bac8 !important;
    font-size: 0.86rem !important;
    text-align: center !important;
}}

footer {{ display: none !important; }}

@media (max-width: 640px) {{
    body::before {{
        opacity: 0.14;
        background-position: center right;
        background-size: 88vw auto;
    }}

    .gradio-container {{
        margin: 0 !important;
        border-radius: 0 !important;
    }}
}}
"""


def load_movies(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load the UTF-8 catalog and derive genre-only profiles for the model."""
    if not dataset_path.is_file():
        raise FileNotFoundError(
            f"Movie catalog not found: {dataset_path}. "
            "Run `python inject_dataset.py` to generate it."
        )

    raw = pd.read_csv(
        dataset_path,
        sep="|",
        header=None,
        encoding="utf-8",
        dtype="string",
        keep_default_na=False,
    )
    if raw.shape[1] != len(DATASET_COLUMNS):
        raise ValueError(
            f"Expected {len(DATASET_COLUMNS)} columns in {dataset_path}, "
            f"found {raw.shape[1]}. Regenerate it with `python inject_dataset.py`."
        )
    raw.columns = DATASET_COLUMNS
    raw["title"] = raw["title"].str.strip()
    raw = raw.loc[raw["title"].ne("")].copy()
    if raw.empty:
        raise ValueError(f"Movie catalog is empty: {dataset_path}.")

    raw["movie_id"] = pd.to_numeric(raw["movie_id"], errors="raise").astype("int64")
    for genre in GENRE_NAMES:
        raw[genre] = pd.to_numeric(raw[genre], errors="raise").astype("int8")
        if not raw[genre].isin([0, 1]).all():
            raise ValueError(f"Genre column {genre!r} must contain only 0 or 1.")

    raw["imdb_rating"] = pd.to_numeric(
        raw["imdb_rating"].replace("", pd.NA), errors="raise"
    )
    if not raw["imdb_rating"].dropna().between(0, 10).all():
        raise ValueError("IMDb seed ratings must be between 0 and 10.")
    raw["imdb_votes"] = pd.to_numeric(
        raw["imdb_votes"].replace("", pd.NA), errors="raise"
    ).astype("Int64")
    if (raw["imdb_votes"].dropna() < 0).any():
        raise ValueError("IMDb vote counts cannot be negative.")
    synthetic_flags = pd.to_numeric(raw["is_synthetic"], errors="raise")
    if not synthetic_flags.isin([0, 1]).all():
        raise ValueError("Synthetic-title flags must contain only 0 or 1.")
    raw["is_synthetic"] = synthetic_flags.astype("int8").astype(bool)
    if (raw["is_synthetic"] & raw["imdb_rating"].notna()).any() or (
        raw["is_synthetic"] & raw["imdb_votes"].notna()
    ).any():
        raise ValueError("Generated titles must not contain IMDb ratings or votes.")
    raw["industry"] = raw["industry"].str.strip()
    raw["profile"] = raw["profile"].str.strip()

    genre_matrix = raw[GENRE_NAMES].to_numpy(dtype=np.int8, copy=False)
    genre_words = np.asarray(GENRE_NAMES, dtype=object)
    metadata_profiles: list[str] = []
    for genre_row in genre_matrix:
        active_genres = genre_words[genre_row == 1]
        metadata_profiles.append(
            " ".join(active_genres) if active_genres.size else "unknown"
        )
    raw["metadata"] = metadata_profiles

    return raw.drop_duplicates(subset=["title"], keep="first").reset_index(drop=True)


class MovieRecommender:
    """Genre-based TF-IDF recommender with title and category search modes."""

    def __init__(self, movies: pd.DataFrame) -> None:
        if movies.empty:
            raise ValueError("The movie dataset is empty.")
        if "metadata" not in movies or "title" not in movies:
            raise ValueError("Movie data must contain title and metadata columns.")

        self.movies = movies.reset_index(drop=True)
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(self.movies["metadata"])
        self.similarity_matrix = linear_kernel(
            self.tfidf_matrix, self.tfidf_matrix
        )
        self.indices = pd.Series(
            self.movies.index, index=self.movies["title"]
        ).to_dict()

    def _format_movie(self, index: int) -> str:
        movie = self.movies.iloc[index]
        title = str(movie["title"])
        if bool(movie.get("is_synthetic", False)):
            return f"🎬 {title} · generated title · no verified IMDb data"

        details: list[str] = []
        rating = movie.get("imdb_rating")
        votes = movie.get("imdb_votes")
        industry = movie.get("industry")
        if rating is not None and not pd.isna(rating):
            details.append(f"IMDb seed rating {float(rating):.1f}/10")
        if votes is not None and not pd.isna(votes):
            details.append(f"{int(votes):,} votes")
        if industry and not pd.isna(industry):
            details.append(str(industry))
        suffix = f" · {' · '.join(details)}" if details else ""
        return f"🎬 {title}{suffix}"

    def recommend_by_movie(
        self, movie_title: str, count: int = 5
    ) -> list[str]:
        if movie_title not in self.indices:
            return ["Movie not found. Choose a title from the searchable list."]
        if count < 1:
            raise ValueError("Recommendation count must be at least 1.")

        movie_index = self.indices[movie_title]
        ranked = sorted(
            (
                (index, float(score))
                for index, score in enumerate(self.similarity_matrix[movie_index])
                if index != movie_index
            ),
            key=lambda item: (-item[1], str(self.movies.iloc[item[0]]["title"]).casefold()),
        )
        return [self._format_movie(index) for index, _ in ranked[:count]]

    def recommend_by_genres(
        self, selected_genres: list[str] | None, count: int = 5
    ) -> list[str]:
        if not selected_genres:
            return ["Select at least one genre to get recommendations."]
        if count < 1:
            raise ValueError("Recommendation count must be at least 1.")

        valid_genres = set(GENRE_NAMES) - {"unknown"}
        invalid_genres = set(selected_genres) - valid_genres
        if invalid_genres:
            raise ValueError(f"Unknown genre selection: {', '.join(sorted(invalid_genres))}.")

        query = self.vectorizer.transform([" ".join(selected_genres)])
        scores = linear_kernel(query, self.tfidf_matrix).ravel()
        ranked = sorted(
            (
                (index, float(score))
                for index, score in enumerate(scores)
                if score > 0
            ),
            key=lambda item: (-item[1], str(self.movies.iloc[item[0]]["title"]).casefold()),
        )
        if not ranked:
            return ["No movies matched those genres. Try another combination."]
        return [self._format_movie(index) for index, _ in ranked[:count]]

    def recommend(
        self,
        mode: str,
        selected_movie: str | None,
        selected_genres: list[str] | None,
        count: int | float = 5,
    ) -> list[str]:
        if not float(count).is_integer():
            raise ValueError("Recommendation count must be a whole number.")
        limit = int(count)
        if mode == MOVIE_MODE:
            if not selected_movie:
                return ["Select a movie to get recommendations."]
            return self.recommend_by_movie(selected_movie, limit)
        if mode == GENRE_MODE:
            return self.recommend_by_genres(selected_genres, limit)
        raise ValueError(f"Unknown recommendation mode: {mode!r}.")


def hybrid_recommendation_handler(
    mode: str,
    selected_movie: str | None,
    selected_genres: list[str] | None,
    count: int | float,
    recommender: MovieRecommender,
) -> list[str]:
    return recommender.recommend(mode, selected_movie, selected_genres, count)


def format_recommendations_html(recommendations: list[str]) -> str:
    items = "".join(
        f"<li>{html.escape(recommendation)}</li>"
        for recommendation in recommendations
    )
    return f'<ol class="recommendation-list">{items}</ol>'


def toggle_input_visibility(mode: str) -> tuple[dict[str, bool], dict[str, bool]]:
    if mode == MOVIE_MODE:
        return gr.update(visible=True), gr.update(visible=False)
    if mode == GENRE_MODE:
        return gr.update(visible=False), gr.update(visible=True)
    raise ValueError(f"Unknown recommendation mode: {mode!r}.")


def create_app(recommender: MovieRecommender) -> gr.Blocks:
    titles = sorted(recommender.indices, key=str.casefold)
    if not titles:
        raise ValueError("Cannot create the app without movie titles.")

    blocks_options: dict[str, object] = {"title": "MoodMatcher AI Engine"}
    if BLOCKS_ACCEPTS_CSS and not LAUNCH_ACCEPTS_CSS:
        blocks_options["css"] = NETFLIX_THEME_CSS
    with gr.Blocks(**blocks_options) as demo:
        gr.Markdown("# MoodMatcher AI Engine", elem_id="moodmatcher-title")
        gr.Markdown(
            "Find your next favorite across Bollywood, Tollywood, Hollywood, "
            "and regional cinema. Explore by a film you loved or by genre.",
            elem_id="moodmatcher-subtitle",
        )
        gr.Markdown(
            "**Data note:** Ratings and vote counts are seed-catalog values, "
            "not live-verified IMDb data. Generated title variants are labeled "
            "and have no IMDb statistics."
        )

        with gr.Row():
            with gr.Column():
                mode_selector = gr.Radio(
                    choices=[MOVIE_MODE, GENRE_MODE],
                    value=MOVIE_MODE,
                    label="Choose your discovery mode",
                )
                movie_dropdown = gr.Dropdown(
                    choices=titles,
                    value=next(
                        (title for title in titles if title == "Toy Story (1995)"),
                        titles[0],
                    ),
                    label="Search for a movie you have seen",
                    filterable=True,
                    visible=True,
                )
                genre_selector = gr.CheckboxGroup(
                    choices=[genre for genre in GENRE_NAMES if genre != "unknown"],
                    label="Choose one or more genres",
                    visible=False,
                )
                recommendation_count = gr.Slider(
                    minimum=1,
                    maximum=10,
                    step=1,
                    value=5,
                    label="Number of recommendations",
                )
                submit_button = gr.Button(
                    "Find my next movie", variant="primary"
                )
            with gr.Column():
                results = gr.HTML(
                    label="Your recommendations",
                    elem_id="recommendation-results",
                )

        mode_selector.change(
            fn=toggle_input_visibility,
            inputs=mode_selector,
            outputs=[movie_dropdown, genre_selector],
        )
        submit_button.click(
            fn=lambda mode, movie, genres, count: format_recommendations_html(
                hybrid_recommendation_handler(
                    mode, movie, genres, count, recommender
                )
            ),
            inputs=[
                mode_selector,
                movie_dropdown,
                genre_selector,
                recommendation_count,
            ],
            outputs=results,
        )
        gr.Markdown(
            "**Created by:** Dnyaneshwar Khedkar · Harshal Kandekar · "
            "Samarth Laware · Vaibhav Mundhe",
            elem_id="credits",
        )

    return demo


gradio_interface = create_app(MovieRecommender(load_movies()))
app = gr.mount_gradio_app(FastAPI(), gradio_interface, path="/")


def main() -> None:
    launch_options: dict[str, object] = {
        "share": False,
        "server_name": "127.0.0.1",
    }
    if LAUNCH_ACCEPTS_CSS:
        launch_options["css"] = NETFLIX_THEME_CSS
    if BACKGROUND_IMAGE_PATHS:
        launch_options["allowed_paths"] = [
            str(image_path) for image_path in BACKGROUND_IMAGE_PATHS
        ]
    if "css" in inspect.signature(gradio_interface.launch).parameters:
        launch_options["css"] = NETFLIX_THEME_CSS
    gradio_interface.launch(**launch_options)


if __name__ == "__main__":
    main()
