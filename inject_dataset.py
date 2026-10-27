import codecs
import csv
import random
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

# ============================================================
# MOVIELENS GENRE MAP (19 CATEGORIES)
# ============================================================
GENRE_MAP = {
    'unknown': 0, 'Action': 1, 'Adventure': 2, 'Animation': 3, 'Childrens': 4,
    'Comedy': 5, 'Crime': 6, 'Documentary': 7, 'Drama': 8, 'Fantasy': 9,
    'Film-Noir': 10, 'Horror': 11, 'Musical': 12, 'Mystery': 13, 'Romance': 14,
    'Sci-Fi': 15, 'Thriller': 16, 'War': 17, 'Western': 18
}

GENRE_ALIASES = {
    "Biography": "Drama",
    "Family": "Childrens",
    "History": "Drama",
    "Music": "Musical",
    "Sport": "Action",
}
INDUSTRY_STARTS = {
    "3 Idiots (2009)": "Bollywood",
    "Baahubali: The Beginning (2015)": "Tollywood",
    "The Shawshank Redemption (1994)": "Hollywood",
    "Sairat (2016)": "Marathi",
    "Vikram (2022)": "Tamil",
    "Drishyam (2013)": "Malayalam",
    "K.G.F: Chapter 1 (2018)": "Kannada",
}
PREFIXES = ("The Legend of", "Rise of", "Legacy of")
SUFFIXES = ("Chapter 2", "Evolution", "Unleashed")
TARGET_DATASET_SIZE = 225
OUTPUT_PATH = Path(__file__).with_name("u.item")


@dataclass(frozen=True)
class MovieRecord:
    title: str
    genres: tuple[str, ...]
    rating: float | None
    votes: int | None
    industry: str
    is_synthetic: bool = False


# ============================================================
# MOVIE DATABASE (YOUR FULL SOURCE CATALOG)
# ============================================================
movies = [
    # ---------------- BOLLYWOOD ----------------
    ("3 Idiots (2009)", ["Comedy", "Drama"], 8.4, 450000),
    ("Dangal (2016)", ["Drama", "Action"], 8.3, 220000),
    ("Taare Zameen Par (2007)", ["Drama", "Childrens"], 8.3, 200000),
    ("Lagaan (2001)", ["Drama", "Musical", "Adventure"], 8.1, 120000),
    ("Swades (2004)", ["Drama"], 8.2, 100000),
    ("Munna Bhai M.B.B.S. (2003)", ["Comedy", "Drama"], 8.1, 85000),
    ("Hera Pheri (2000)", ["Comedy"], 8.2, 70000),
    ("Andaz Apna Apna (1994)", ["Comedy", "Romance"], 8.0, 60000),
    ("Sholay (1975)", ["Action", "Adventure", "Drama"], 8.1, 60000),
    ("Dilwale Dulhania Le Jayenge (1995)", ["Romance", "Drama", "Musical"], 8.0, 75000),
    ("Rang De Basanti (2006)", ["Drama"], 8.1, 125000),
    ("Chak De! India (2007)", ["Drama"], 8.1, 85000),
    ("Queen (2013)", ["Comedy", "Drama"], 8.1, 70000),
    ("Barfi! (2012)", ["Comedy", "Drama", "Romance"], 8.1, 82000),
    ("Kahaani (2012)", ["Thriller", "Mystery"], 8.1, 65000),
    ("Andhadhun (2018)", ["Thriller", "Mystery", "Comedy"], 8.2, 110000),
    ("Drishyam (2015)", ["Thriller", "Mystery", "Crime"], 8.2, 98000),
    ("A Wednesday! (2008)", ["Thriller", "Drama"], 8.1, 80000),
    ("Gangs of Wasseypur (2012)", ["Crime", "Drama", "Action"], 8.2, 95000),
    ("Special 26 (2013)", ["Crime", "Drama", "Thriller"], 8.0, 58000),
    ("Uri: The Surgical Strike (2019)", ["Action", "War", "Thriller"], 8.2, 62000),
    ("Raazi (2018)", ["Thriller", "Drama", "War"], 7.7, 33000),
    ("Bajrangi Bhaijaan (2015)", ["Drama", "Adventure"], 8.1, 95000),
    ("PK (2014)", ["Comedy", "Drama", "Fantasy"], 8.1, 200000),
    ("Chhichhore (2019)", ["Comedy", "Drama"], 8.3, 65000),
    ("Bhaag Milkha Bhaag (2013)", ["Drama"], 8.2, 75000),
    ("Jab We Met (2007)", ["Romance", "Comedy"], 7.9, 72000),
    ("Yeh Jawaani Hai Deewani (2013)", ["Romance", "Comedy", "Musical"], 7.3, 50000),
    ("Rockstar (2011)", ["Drama", "Musical", "Romance"], 7.7, 55000),
    ("Zindagi Na Milegi Dobara (2011)", ["Comedy", "Drama"], 8.2, 80000),
    ("Dil Chahta Hai (2001)", ["Comedy", "Drama", "Romance"], 8.1, 75000),
    ("Swatantrya Veer Savarkar (2024)", ["Drama"], 7.6, 15000),
    ("12th Fail (2023)", ["Drama"], 8.8, 100000),
    ("Laapataa Ladies (2024)", ["Comedy", "Drama"], 8.4, 40000),
    ("Stree (2018)", ["Comedy", "Horror"], 7.5, 40000),
    ("Tumbbad (2018)", ["Drama", "Fantasy", "Horror"], 8.2, 65000),
    ("M.S. Dhoni: The Untold Story (2016)", ["Drama"], 8.0, 65000),
    ("Pink (2016)", ["Drama", "Thriller"], 8.1, 55000),
    ("Article 15 (2019)", ["Crime", "Drama"], 8.1, 40000),
    ("Sardar Udham (2021)", ["Drama"], 8.4, 45000),
    ("Shershaah (2021)", ["Action", "Drama", "War"], 8.3, 40000),
    ("Maqbool (2003)", ["Crime", "Drama"], 8.0, 15000),
    ("Omkara (2006)", ["Crime", "Drama"], 8.1, 20000),
    ("Haider (2014)", ["Crime", "Drama", "Thriller"], 8.0, 55000),
    ("English Vinglish (2012)", ["Comedy", "Drama"], 7.8, 35000),
    ("Piku (2015)", ["Comedy", "Drama"], 7.6, 35000),
    ("Airlift (2016)", ["Drama"], 7.9, 45000),
    ("Baby (2015)", ["Action", "Thriller"], 7.9, 50000),
    ("Welcome (2007)", ["Comedy"], 7.0, 35000),

    # ---------------- TOLLYWOOD ----------------
    ("Baahubali: The Beginning (2015)", ["Action", "Adventure", "Drama"], 8.0, 120000),
    ("Baahubali 2: The Conclusion (2017)", ["Action", "Drama"], 8.2, 110000),
    ("RRR (2022)", ["Action", "Drama"], 7.8, 100000),
    ("Eega (2012)", ["Action", "Fantasy"], 7.7, 25000),
    ("Magadheera (2009)", ["Action", "Fantasy", "Romance"], 7.7, 20000),
    ("Pokiri (2006)", ["Action", "Thriller"], 8.0, 20000),
    ("Athadu (2005)", ["Action", "Thriller"], 8.2, 20000),
    ("Ala Vaikunthapurramuloo (2020)", ["Action", "Comedy", "Drama"], 7.3, 25000),
    ("Arjun Reddy (2017)", ["Drama", "Romance"], 7.9, 35000),
    ("Mahanati (2018)", ["Drama"], 8.4, 25000),
    ("Jersey (2019)", ["Drama"], 8.5, 30000),
    ("Rangasthalam (2018)", ["Action", "Drama"], 8.2, 25000),
    ("Pushpa: The Rise (2021)", ["Action", "Crime", "Drama"], 7.6, 50000),
    ("Pushpa 2: The Rule (2024)", ["Action", "Crime", "Drama"], 6.0, 25000),
    ("Salaar: Part 1 – Ceasefire (2023)", ["Action", "Thriller"], 6.5, 30000),
    ("Kalki 2898 AD (2024)", ["Action", "Adventure", "Sci-Fi"], 7.0, 40000),
    ("Srimanthudu (2015)", ["Action", "Drama"], 7.5, 15000),
    ("Bharat Ane Nenu (2018)", ["Action", "Drama"], 7.5, 15000),
    ("Janatha Garage (2016)", ["Action", "Drama"], 7.2, 12000),
    ("Manam (2014)", ["Comedy", "Drama", "Fantasy"], 8.0, 18000),
    ("C/o Kancharapalem (2018)", ["Drama", "Romance"], 8.8, 12000),
    ("Agent Sai Srinivasa Athreya (2019)", ["Comedy", "Crime", "Mystery"], 8.3, 12000),
    ("Goodachari (2018)", ["Action", "Thriller"], 7.8, 15000),
    ("Sita Ramam (2022)", ["Drama", "Romance"], 8.5, 30000),
    ("Hi Nanna (2023)", ["Drama", "Romance"], 8.2, 15000),
    ("Dasara (2023)", ["Action", "Drama"], 6.6, 12000),
    ("Hanuman (2024)", ["Action", "Adventure", "Fantasy"], 7.8, 15000),
    ("Karthikeya 2 (2022)", ["Action", "Adventure", "Fantasy"], 7.8, 20000),
    ("Major (2022)", ["Action", "Drama"], 8.1, 15000),
    ("Pelli Choopulu (2016)", ["Comedy", "Romance"], 8.0, 12000),

    # ---------------- HOLLYWOOD ----------------
    ("The Shawshank Redemption (1994)", ["Drama"], 9.3, 3000000),
    ("The Godfather (1972)", ["Crime", "Drama"], 9.2, 2100000),
    ("The Godfather Part II (1974)", ["Crime", "Drama"], 9.0, 1400000),
    ("The Dark Knight (2008)", ["Action", "Crime", "Drama"], 9.0, 3000000),
    ("12 Angry Men (1957)", ["Drama"], 9.0, 900000),
    ("Schindler's List (1993)", ["Drama", "War"], 9.0, 1500000),
    ("Pulp Fiction (1994)", ["Crime", "Drama"], 8.9, 2300000),
    ("The Lord of the Rings: The Return of the King (2003)", ["Action", "Adventure", "Fantasy"], 9.0, 2000000),
    ("Forrest Gump (1994)", ["Drama", "Romance"], 8.8, 2300000),
    ("Inception (2010)", ["Action", "Sci-Fi", "Thriller"], 8.8, 2600000),
    ("The Matrix (1999)", ["Action", "Sci-Fi"], 8.7, 2100000),
    ("Interstellar (2014)", ["Adventure", "Drama", "Sci-Fi"], 8.7, 2300000),
    ("The Prestige (2006)", ["Drama", "Mystery", "Sci-Fi"], 8.5, 1500000),
    ("Fight Club (1999)", ["Drama", "Thriller"], 8.8, 2400000),
    ("Goodfellas (1990)", ["Crime", "Drama"], 8.7, 1300000),
    ("Se7en (1995)", ["Crime", "Drama", "Mystery"], 8.6, 1800000),
    ("The Silence of the Lambs (1991)", ["Crime", "Drama", "Thriller"], 8.6, 1600000),
    ("Saving Private Ryan (1998)", ["Drama", "War"], 8.6, 1500000),
    ("The Green Mile (1999)", ["Crime", "Drama", "Fantasy"], 8.6, 1400000),
    ("Gladiator (2000)", ["Action", "Adventure", "Drama"], 8.5, 1700000),
    ("Titanic (1997)", ["Drama", "Romance"], 7.9, 1300000),
    ("Avatar (2009)", ["Action", "Adventure", "Fantasy"], 7.9, 1500000),
    ("Jurassic Park (1993)", ["Adventure", "Sci-Fi", "Thriller"], 8.2, 1100000),
    ("Back to the Future (1985)", ["Adventure", "Comedy", "Sci-Fi"], 8.5, 1300000),
    ("Terminator 2: Judgment Day (1991)", ["Action", "Sci-Fi"], 8.6, 1200000),
    ("The Avengers (2012)", ["Action", "Adventure", "Sci-Fi"], 8.0, 1500000),
    ("Avengers: Infinity War (2018)", ["Action", "Adventure", "Sci-Fi"], 8.4, 1200000),
    ("Avengers: Endgame (2019)", ["Action", "Adventure", "Drama"], 8.4, 1300000),
    ("Iron Man (2008)", ["Action", "Adventure", "Sci-Fi"], 7.9, 1200000),
    ("Black Panther (2018)", ["Action", "Adventure", "Sci-Fi"], 7.3, 850000),
    ("Spider-Man: No Way Home (2021)", ["Action", "Adventure", "Fantasy"], 8.2, 900000),
    ("Joker (2019)", ["Crime", "Drama", "Thriller"], 8.3, 1600000),
    ("Oppenheimer (2023)", ["Biography", "Drama", "History"], 8.3, 850000),
    ("Dune (2021)", ["Action", "Adventure", "Drama"], 8.0, 900000),
    ("The Lion King (1994)", ["Animation", "Adventure", "Drama"], 8.5, 1100000),
    ("Toy Story (1995)", ["Animation", "Adventure", "Comedy"], 8.3, 1100000),
    ("Finding Nemo (2003)", ["Animation", "Adventure", "Comedy"], 8.2, 1100000),
    ("WALL-E (2008)", ["Animation", "Adventure", "Family"], 8.4, 1200000),
    ("Up (2009)", ["Animation", "Adventure", "Comedy"], 8.3, 1200000),
    ("Coco (2017)", ["Animation", "Adventure", "Family"], 8.4, 600000),
    ("Inside Out (2015)", ["Animation", "Adventure", "Comedy"], 8.1, 800000),
    ("Shrek (2001)", ["Animation", "Adventure", "Comedy"], 7.9, 750000),
    ("Frozen (2013)", ["Animation", "Adventure", "Comedy"], 7.4, 700000),
    ("The Truman Show (1998)", ["Comedy", "Drama", "Sci-Fi"], 8.2, 1200000),
    ("The Social Network (2010)", ["Biography", "Drama"], 7.8, 700000),
    ("The Wolf of Wall Street (2013)", ["Biography", "Comedy", "Crime"], 8.2, 1600000),
    ("Catch Me If You Can (2002)", ["Biography", "Crime", "Drama"], 8.1, 1100000),
    ("The Departed (2006)", ["Crime", "Drama", "Thriller"], 8.5, 1400000),
    ("Memento (2000)", ["Mystery", "Thriller"], 8.4, 1300000),
    ("Shutter Island (2010)", ["Mystery", "Thriller"], 8.2, 1500000),
    ("Gone Girl (2014)", ["Drama", "Mystery", "Thriller"], 8.1, 1100000),
    ("The Sixth Sense (1999)", ["Drama", "Mystery", "Thriller"], 8.2, 1100000),
    ("The Conjuring (2013)", ["Horror", "Mystery", "Thriller"], 7.5, 600000),
    ("Get Out (2017)", ["Horror", "Mystery", "Thriller"], 7.8, 700000),
    ("Rocky (1976)", ["Drama", "Sport"], 8.1, 650000),
    ("Whiplash (2014)", ["Drama", "Music"], 8.5, 1000000),
    ("La La Land (2016)", ["Comedy", "Drama", "Musical"], 8.0, 700000),
    ("The Grand Budapest Hotel (2014)", ["Adventure", "Comedy", "Crime"], 8.1, 900000),

    # ---------------- MARATHI ----------------

    ("Sairat (2016)", ["Romance", "Drama", "Musical"], 8.3, 15000),
    ("Natsamrat (2016)", ["Drama"], 8.8, 12000),
    ("Court (2014)", ["Drama"], 8.1, 6000),
    ("Fandry (2013)", ["Drama"], 8.0, 3500),
    ("Killa (2014)", ["Drama", "Childrens"], 8.0, 4000),
    ("Harishchandrachi Factory (2009)", ["Drama"], 8.4, 5000),
    ("Ashi Hi Banwa Banwi (1988)", ["Comedy"], 8.6, 4500),
    ("Duniyadari (2013)", ["Romance", "Comedy", "Drama"], 7.7, 3500),
    ("Timepass (2014)", ["Romance", "Comedy"], 7.1, 2800),
    ("Timepass 2 (2015)", ["Romance", "Comedy"], 6.5, 1500),
    ("Balak Palak (2013)", ["Comedy", "Drama"], 7.5, 3800),
    ("De Dhakka (2008)", ["Comedy", "Drama"], 7.4, 1800),
    ("Zapatlela (1993)", ["Comedy", "Horror"], 7.6, 2500),
    ("Mulshi Pattern (2018)", ["Crime", "Drama", "Action"], 8.1, 5500),
    ("Anandi Gopal (2019)", ["Drama"], 8.3, 4000),
    ("Pawankhind (2022)", ["Action", "Drama"], 8.2, 6000),
    ("Sher Shivraj (2022)", ["Action", "Drama"], 7.3, 2500),
    ("Farzand (2018)", ["Action", "Drama"], 7.5, 2500),
    ("Faster Fene (2017)", ["Mystery", "Thriller", "Crime"], 8.1, 5000),
    ("Rege (2014)", ["Crime", "Drama", "Thriller"], 7.7, 2000),
    ("Elizabeth Ekadashi (2014)", ["Drama"], 7.9, 1800),
    ("Katyar Kaljat Ghusali (2015)", ["Drama", "Musical"], 8.3, 3000),
    ("Natarang (2010)", ["Drama", "Musical"], 8.7, 2500),
    ("Jogwa (2009)", ["Drama"], 7.8, 1500),
    ("Dombivli Fast (2005)", ["Drama", "Thriller"], 8.3, 1800),
    ("Shwaas (2004)", ["Drama"], 8.3, 1800),
    ("Deool (2011)", ["Comedy", "Drama"], 7.8, 1800),
    ("Double Seat (2015)", ["Drama", "Romance"], 7.4, 1200),
    ("Mumbai Pune Mumbai (2010)", ["Romance", "Comedy"], 7.2, 1800),
    ("Baipan Bhari Deva (2023)", ["Drama"], 7.7, 2500),
    ("Jhimma (2021)", ["Comedy", "Drama"], 7.5, 1500),
    ("Ved (2022)", ["Romance", "Drama"], 7.2, 2000),
    ("Vaalvi (2023)", ["Comedy", "Thriller"], 7.8, 2500),
    ("Naal (2018)", ["Drama"], 8.0, 1500),
    ("Aatmapamphlet (2023)", ["Comedy", "Drama"], 7.8, 1000),
    ("Gulabjaam (2018)", ["Drama"], 7.5, 1200),
    ("Muramba (2017)", ["Romance", "Comedy"], 7.5, 1500),
    ("Classmates (2015)", ["Drama", "Mystery"], 6.8, 1200),
    ("Lai Bhaari (2014)", ["Action", "Drama"], 7.0, 2500),
    ("Balgandharva (2011)", ["Biography", "Drama", "Musical"], 7.8, 1200),

    # ---------------- TAMIL ----------------

    ("Vikram (2022)", ["Action", "Thriller"], 8.3, 65000),
    ("Kaithi (2019)", ["Action", "Thriller"], 8.4, 35000),
    ("Vikram Vedha (2017)", ["Action", "Crime", "Thriller"], 8.2, 35000),
    ("96 (2018)", ["Drama", "Romance"], 8.5, 25000),
    ("Soorarai Pottru (2020)", ["Drama"], 8.7, 30000),
    ("Jai Bhim (2021)", ["Crime", "Drama"], 8.7, 30000),
    ("Asuran (2019)", ["Action", "Drama"], 8.4, 25000),
    ("Pariyerum Perumal (2018)", ["Drama"], 8.7, 15000),
    ("Super Deluxe (2019)", ["Crime", "Drama", "Thriller"], 8.2, 20000),
    ("Anbe Sivam (2003)", ["Comedy", "Drama"], 8.6, 15000),
    ("Nayakan (1987)", ["Crime", "Drama"], 8.6, 20000),
    ("Enthiran (2010)", ["Action", "Sci-Fi"], 7.1, 30000),
    ("Ponniyin Selvan: I (2022)", ["Action", "Drama"], 7.6, 25000),
    ("Ponniyin Selvan: II (2023)", ["Action", "Drama"], 7.3, 18000),
    ("Ghilli (2004)", ["Action", "Romance"], 8.1, 15000),

    # ---------------- MALAYALAM ----------------

    ("Drishyam (2013)", ["Crime", "Drama", "Thriller"], 8.6, 45000),
    ("Drishyam 2 (2021)", ["Crime", "Drama", "Thriller"], 8.4, 30000),
    ("Manjummel Boys (2024)", ["Adventure", "Drama", "Thriller"], 8.2, 20000),
    ("Premam (2015)", ["Comedy", "Drama", "Romance"], 8.3, 20000),
    ("Bangalore Days (2014)", ["Comedy", "Drama", "Romance"], 8.3, 20000),
    ("Kumbalangi Nights (2019)", ["Comedy", "Drama", "Romance"], 8.5, 20000),
    ("The Great Indian Kitchen (2021)", ["Drama"], 8.1, 12000),
    ("2018 (2023)", ["Drama", "Thriller"], 7.7, 15000),
    ("Aavesham (2024)", ["Action", "Comedy"], 7.8, 12000),
    ("Lucifer (2019)", ["Action", "Crime", "Drama"], 7.5, 15000),
    ("Jana Gana Mana (2022)", ["Crime", "Drama", "Thriller"], 8.3, 12000),
    ("Uyare (2019)", ["Drama"], 8.0, 10000),
    ("Minnal Murali (2021)", ["Action", "Comedy", "Fantasy"], 7.8, 15000),
    ("Charlie (2015)", ["Adventure", "Drama", "Romance"], 8.0, 12000),
    ("Maheshinte Prathikaaram (2016)", ["Comedy", "Drama"], 8.3, 12000),

    # ---------------- KANNADA ----------------

    ("K.G.F: Chapter 1 (2018)", ["Action", "Crime", "Drama"], 8.2, 50000),
    ("K.G.F: Chapter 2 (2022)", ["Action", "Crime", "Drama"], 8.2, 45000),
    ("Kantara (2022)", ["Action", "Drama", "Thriller"], 8.2, 30000),
    ("777 Charlie (2022)", ["Adventure", "Comedy", "Drama"], 8.7, 25000),
    ("Ugramm (2014)", ["Action", "Crime", "Drama"], 7.5, 5000),
    ("Lucia (2013)", ["Drama", "Mystery", "Sci-Fi"], 8.3, 10000),
    ("RangiTaranga (2015)", ["Mystery", "Thriller"], 8.2, 8000),
    ("Garuda Gamana Vrishabha Vahana (2021)", ["Crime", "Drama"], 8.2, 8000),
    ("Mungaru Male (2006)", ["Romance", "Drama"], 8.3, 7000),
    ("Kirik Party (2016)", ["Comedy", "Drama", "Romance"], 8.0, 8000)
]

def _normalized_genres(genres: Sequence[str]) -> tuple[str, ...]:
    normalized: list[str] = []
    for genre in genres:
        mapped = GENRE_ALIASES.get(genre, genre)
        if mapped not in GENRE_MAP:
            raise ValueError(f"Unsupported genre {genre!r}.")
        if mapped != "unknown" and mapped not in normalized:
            normalized.append(mapped)
    return tuple(normalized or ["unknown"])


def build_dataset_records(
    source_movies: Sequence[tuple[str, Sequence[str], float, int]] = movies,
    target_size: int = TARGET_DATASET_SIZE,
    rng: random.Random | None = None,
) -> list[MovieRecord]:
    """Build unique records, marking generated title variants as synthetic."""
    if not source_movies:
        raise ValueError("The source movie catalog must not be empty.")
    if target_size < 0:
        raise ValueError("The target dataset size cannot be negative.")
    if len({title.casefold() for title, _, _, _ in source_movies}) != len(source_movies):
        raise ValueError("The source movie catalog contains duplicate titles.")

    generator = rng or random.Random(42)
    records: list[MovieRecord] = []
    industry = "Indian Regional"
    for title, genres, rating, votes in source_movies:
        if not title.strip():
            raise ValueError("Movie titles must not be empty.")
        if not 0 <= float(rating) <= 10:
            raise ValueError(f"IMDb seed rating for {title!r} must be between 0 and 10.")
        if int(votes) < 0:
            raise ValueError(f"IMDb vote count for {title!r} cannot be negative.")
        industry = INDUSTRY_STARTS.get(title, industry)
        records.append(
            MovieRecord(
                title=title,
                genres=_normalized_genres(genres),
                rating=float(rating),
                votes=int(votes),
                industry=industry,
            )
        )

    if len(records) >= target_size:
        return records

    used_titles = {record.title.casefold() for record in records}
    attempts = 0
    maximum_attempts = max(1000, (target_size - len(records)) * len(records) * 50)
    while len(records) < target_size and attempts < maximum_attempts:
        attempts += 1
        base = generator.choice(records[: len(source_movies)])
        match = re.match(r"^(.*?)(?:\s+\((\d{4})\))?$", base.title)
        if match is None:
            raise ValueError(f"Could not parse movie title {base.title!r}.")
        base_title, year = match.groups()
        if generator.choice((True, False)):
            variant_title = f"{generator.choice(PREFIXES)} {base_title}"
        else:
            variant_title = f"{base_title}: {generator.choice(SUFFIXES)}"
        if year:
            variant_title = f"{variant_title} ({year})"

        if variant_title.casefold() in used_titles:
            continue
        used_titles.add(variant_title.casefold())
        records.append(
            MovieRecord(
                title=variant_title,
                genres=base.genres,
                rating=None,
                votes=None,
                industry=base.industry,
                is_synthetic=True,
            )
        )

    if len(records) < target_size:
        raise ValueError(
            f"Could only generate {len(records)} unique titles; "
            f"{target_size} were requested."
        )
    return records


def _profile_for(record: MovieRecord) -> str:
    genre_text = ", ".join(
        genre for genre in record.genres if genre != "unknown"
    ) or "Unknown"
    if record.is_synthetic:
        rating_text = "generated variant; no verified IMDb rating or vote count"
    else:
        rating_text = (
            f"IMDb seed rating {record.rating:.1f}/10; "
            f"{record.votes:,} seed votes; values not live-verified"
        )
    return (
        f"genres={genre_text}; industry={record.industry}; "
        f"{rating_text}"
    )


def _row_for(record: MovieRecord, movie_id: int) -> list[str | int | float]:
    genre_bits = [0] * len(GENRE_MAP)
    for genre in record.genres:
        genre_bits[GENRE_MAP[genre]] = 1

    year_match = re.search(r"\((\d{4})\)$", record.title)
    release_date = f"01-Jan-{year_match.group(1)}" if year_match else ""
    return [
        movie_id,
        record.title,
        release_date,
        "",
        "",
        *genre_bits,
        "" if record.rating is None else f"{record.rating:.1f}",
        "" if record.votes is None else record.votes,
        record.industry,
        int(record.is_synthetic),
        _profile_for(record),
    ]


def write_dataset(
    records: Sequence[MovieRecord], destination: Path = OUTPUT_PATH
) -> int:
    """Write UTF-8 pipe-delimited rows atomically and return the movie count."""
    if not records:
        raise ValueError("Cannot write an empty movie catalog.")
    titles = [record.title.casefold() for record in records]
    if len(titles) != len(set(titles)):
        raise ValueError("Movie titles must be unique before writing the dataset.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
    try:
        with codecs.open(str(temporary_path), "w", encoding="utf-8") as output_file:
            writer = csv.writer(output_file, delimiter="|", lineterminator="\n")
            for movie_id, record in enumerate(records, start=1):
                writer.writerow(_row_for(record, movie_id))
        temporary_path.replace(destination)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    return len(records)


def main() -> None:
    records = build_dataset_records()
    count = write_dataset(records)
    synthetic_count = sum(record.is_synthetic for record in records)
    print(
        f"Wrote {count} unique movie records to {OUTPUT_PATH} "
        f"({synthetic_count} generated variants without IMDb statistics)."
    )
    print(
        "Seed-catalog IMDb ratings and vote counts are included in each profile "
        "but have not been independently refreshed or verified."
    )


if __name__ == "__main__":
    main()
