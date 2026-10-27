from __future__ import annotations

import csv
import io
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


DATASET_URL = "https://files.grouplens.org/datasets/movielens/ml-100k/u.item"
DATASET_PATH = Path(__file__).with_name("u.item")
EXPECTED_COLUMNS = 24


def validate_dataset(contents: bytes) -> int:
    try:
        text = contents.decode("latin-1")
        rows = csv.reader(io.StringIO(text), delimiter="|")
        row_count = 0
        for line_number, row in enumerate(rows, start=1):
            if len(row) != EXPECTED_COLUMNS or not row[0].isdigit():
                raise ValueError(
                    f"Invalid MovieLens row {line_number}: expected "
                    f"{EXPECTED_COLUMNS} pipe-separated fields."
                )
            row_count += 1
    except csv.Error as error:
        raise ValueError(f"Could not parse MovieLens data: {error}") from error

    if row_count == 0:
        raise ValueError("The downloaded MovieLens dataset is empty.")
    return row_count


def download_dataset(destination: Path = DATASET_PATH) -> int:
    request = Request(
        DATASET_URL,
        headers={"User-Agent": "MovieRecommendationMiniProject/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        contents = response.read()

    row_count = validate_dataset(contents)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=destination.parent,
            prefix=f"{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(contents)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return row_count


if __name__ == "__main__":
    try:
        count = download_dataset()
    except (OSError, URLError, ValueError) as error:
        print(f"Dataset download failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Downloaded and verified {count} movies to {DATASET_PATH}.")
