import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from fastapi import FastAPI

from app import (
    GENRE_MODE,
    MOVIE_MODE,
    NETFLIX_THEME_CSS,
    MovieRecommender,
    app,
    create_app,
    format_recommendations_html,
    load_movies,
    main,
    toggle_input_visibility,
)
from inject_dataset import (
    MovieRecord,
    build_dataset_records,
    write_dataset,
)


GENRE_COUNT = 19


def movie_row(
    movie_id: int,
    title: str,
    active_genres: tuple[int, ...],
    rating: str = "8.0",
    votes: str = "1200",
    industry: str = "Hollywood",
    synthetic: str = "0",
    profile: str = "test profile",
) -> list[str]:
    genres = ["0"] * GENRE_COUNT
    for genre_index in active_genres:
        genres[genre_index] = "1"
    return [
        str(movie_id),
        title,
        "01-Jan-1995",
        "",
        "",
        *genres,
        rating,
        votes,
        industry,
        synthetic,
        profile,
    ]


class DatasetGeneratorTests(unittest.TestCase):
    def test_builds_unique_catalog_with_unrated_generated_variants(self) -> None:
        records = build_dataset_records()
        titles = [record.title.casefold() for record in records]
        synthetic_records = [record for record in records if record.is_synthetic]

        self.assertGreaterEqual(len(records), 210)
        self.assertEqual(len(titles), len(set(titles)))
        self.assertGreaterEqual(len(records) - len(synthetic_records), 45)
        self.assertTrue(synthetic_records)
        self.assertTrue(
            all(record.rating is None and record.votes is None for record in synthetic_records)
        )
        self.assertTrue(
            any(
                record.title.startswith(("The Legend of ", "Rise of ", "Legacy of "))
                for record in synthetic_records
            )
        )
        self.assertTrue(
            any(
                f": {suffix} (" in record.title
                for record in synthetic_records
                for suffix in ("Chapter 2", "Evolution", "Unleashed")
            )
        )

    def test_writes_utf8_extended_movie_format(self) -> None:
        records = [
            MovieRecord(
                title="Café 🎬 (2020)",
                genres=("Action", "Drama"),
                rating=8.1,
                votes=100,
                industry="Bollywood",
            )
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "u.item"
            self.assertEqual(write_dataset(records, path), 1)

            with path.open(encoding="utf-8", newline="") as dataset:
                row = next(csv.reader(dataset, delimiter="|"))

            movies = load_movies(path)

        self.assertEqual(len(row), 29)
        self.assertEqual(movies.iloc[0]["title"], "Café 🎬 (2020)")
        self.assertIn("Action Drama", movies.iloc[0]["metadata"])
        self.assertIn("IMDb seed rating 8.1/10", movies.iloc[0]["profile"])


class MovieDataTests(unittest.TestCase):
    def test_load_movies_creates_genre_profiles_and_reads_ratings(self) -> None:
        rows = [
            movie_row(1, "Alpha (1995)", (1,)),
            movie_row(2, "Beta (1995)", (1, 5), rating="7.5"),
            movie_row(3, "Alpha (1995)", (8,), rating="9.0"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "u.item"
            with path.open("w", encoding="utf-8", newline="") as dataset:
                csv.writer(dataset, delimiter="|", lineterminator="\n").writerows(rows)

            movies = load_movies(path)

        self.assertEqual(movies["title"].tolist(), ["Alpha (1995)", "Beta (1995)"])
        self.assertEqual(movies["metadata"].tolist(), ["Action", "Action Comedy"])
        self.assertEqual(float(movies.iloc[1]["imdb_rating"]), 7.5)
        self.assertEqual(int(movies.iloc[1]["imdb_votes"]), 1200)

    def test_missing_and_malformed_datasets_fail_with_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_path = Path(temp_dir) / "missing.item"
            with self.assertRaisesRegex(FileNotFoundError, "inject_dataset.py"):
                load_movies(missing_path)

            malformed_path = Path(temp_dir) / "malformed.item"
            malformed_path.write_text("not|the|expected|schema\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Regenerate it"):
                load_movies(malformed_path)

    def test_movie_mode_excludes_selected_title_and_ranks_similar_genres(self) -> None:
        movies = pd.DataFrame(
            {
                "title": ["Alpha", "Beta", "Gamma", "Drama"],
                "metadata": ["Action", "Action Comedy", "Action", "Drama"],
                "imdb_rating": [8.0, 7.0, 9.0, 6.0],
                "imdb_votes": [1000, 500, 300, 200],
                "industry": ["Bollywood", "Tollywood", "Hollywood", "Marathi"],
                "is_synthetic": [False, False, False, False],
            }
        )
        recommender = MovieRecommender(movies)

        results = recommender.recommend(MOVIE_MODE, "Alpha", [], 2)

        self.assertTrue(results[0].startswith("🎬 Gamma"))
        self.assertEqual(len(results), 2)
        self.assertNotIn("Alpha", "\n".join(results))
        self.assertIn("IMDb seed rating", results[0])

    def test_genre_mode_handles_empty_and_valid_inputs(self) -> None:
        recommender = MovieRecommender(
            pd.DataFrame(
                {
                    "title": ["Action Film", "Drama Film"],
                    "metadata": ["Action", "Drama"],
                }
            )
        )

        self.assertIn("Select at least one genre", recommender.recommend_by_genres([])[0])
        self.assertTrue(recommender.recommend(GENRE_MODE, None, ["Action"], 1)[0].endswith("Action Film"))

    def test_invalid_requests_and_empty_movie_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "dataset is empty"):
            MovieRecommender(pd.DataFrame(columns=["title", "metadata"]))

        recommender = MovieRecommender(
            pd.DataFrame({"title": ["Only"], "metadata": ["Action"]})
        )
        self.assertIn("Movie not found", recommender.recommend_by_movie("Missing")[0])
        with self.assertRaisesRegex(ValueError, "whole number"):
            recommender.recommend(MOVIE_MODE, "Only", [], 1.5)
        with self.assertRaisesRegex(ValueError, "Unknown genre"):
            recommender.recommend_by_genres(["Not a genre"])

    def test_mode_toggle_and_gradio_app_build(self) -> None:
        movie_visibility, genre_visibility = toggle_input_visibility(MOVIE_MODE)
        self.assertTrue(movie_visibility["visible"])
        self.assertFalse(genre_visibility["visible"])

        movie_visibility, genre_visibility = toggle_input_visibility(GENRE_MODE)
        self.assertFalse(movie_visibility["visible"])
        self.assertTrue(genre_visibility["visible"])

        recommender = MovieRecommender(
            pd.DataFrame({"title": ["Toy Story (1995)"], "metadata": ["Animation Adventure"]})
        )
        self.assertIsNotNone(create_app(recommender))

    def test_vercel_entrypoint_is_fastapi_app(self) -> None:
        self.assertIsInstance(app, FastAPI)

    def test_recommendation_output_is_safe_html(self) -> None:
        rendered = format_recommendations_html(
            ["🎬 Safe Movie", "<script>alert('x')</script>"]
        )

        self.assertIn('<ol class="recommendation-list">', rendered)
        self.assertIn("🎬 Safe Movie", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertNotIn("<script>", rendered)

    def test_theme_keeps_both_local_images_behind_transparent_gradio_layers(self) -> None:
        self.assertIn(
            "linear-gradient(rgba(15, 11, 25, 0.85), rgba(15, 11, 25, 0.96))",
            NETFLIX_THEME_CSS,
        )
        self.assertIn("gradio-app", NETFLIX_THEME_CSS)
        self.assertIn("background: transparent !important", NETFLIX_THEME_CSS)
        self.assertIn("Untitled%20design%20%281%29.jpg", NETFLIX_THEME_CSS)
        self.assertIn("image_f0140cfc.jpg", NETFLIX_THEME_CSS)

    def test_theme_preserves_visible_selected_states_for_modes_and_genres(self) -> None:
        self.assertIn(
            'input:not([type="checkbox"]):not([type="radio"])',
            NETFLIX_THEME_CSS,
        )
        self.assertIn('input[type="checkbox"]:checked', NETFLIX_THEME_CSS)
        self.assertIn('input[type="radio"]:checked', NETFLIX_THEME_CSS)
        self.assertIn("label.selected", NETFLIX_THEME_CSS)
        self.assertIn("var(--checkbox-check)", NETFLIX_THEME_CSS)

    def test_main_passes_css_once_to_gradio_launch(self) -> None:
        with patch("app.gr.Blocks.launch") as launch:
            main()

        self.assertIn("css", launch.call_args.kwargs)
        self.assertFalse(launch.call_args.kwargs["share"])
        self.assertEqual(len(launch.call_args.kwargs["allowed_paths"]), 2)


if __name__ == "__main__":
    unittest.main()
