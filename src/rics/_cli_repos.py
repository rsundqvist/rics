import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    import pandas

_DATETIME_DTYPE = "datetime64[ns, UTC]"
_PUSH = "Last push"
_SORT_COLUMNS = {
    "push": (_PUSH, False),
    "stars": ("Stars", False),
    "created": ("Created", True),
    "name": ("Repo name", True),
}


@click.command("repos")
@click.option(
    "--user",
    "-u",
    help="User or organization on GitHub.",
    default=["rsundqvist"],
    multiple=True,
    show_default=True,
)
@click.option(
    "--max-days",
    "-d",
    type=click.IntRange(min=0),
    help="Max days since the last push.",
)
@click.option(
    "--sort",
    type=click.Choice(sorted(_SORT_COLUMNS), case_sensitive=False),
    help="Column to sort on.",
    default="push",
    show_default=True,
)
@click.option(
    "--max-width",
    type=int,
    help="Maximum width for the 'Description' column. Zero=no limit.",
)
def main(
    max_days: int | None,
    user: tuple[str, ...],
    sort: str,
    max_width: int | None,
) -> None:  # pragma: no coverage
    """Get licenced GitHub repositories with releases."""
    import functools
    import logging
    import sys
    from concurrent.futures import ThreadPoolExecutor
    from time import perf_counter

    import click
    import pandas as pd
    import requests

    from .strings import format_perf_counter

    now = pd.Timestamp.utcnow()
    logger = logging.getLogger(f"{__package__}.{main.name}")

    headers = _get_headers(logger)

    per_page = 100

    start = perf_counter()
    raw = []
    for i, u in enumerate(user, start=1):
        n = 0
        page = 1
        while True:
            response = requests.get(
                f"https://api.github.com/users/{u}/repos?{page=}&{per_page=}",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            user_repos = response.json()

            n_repos = len(user_repos)
            n += n_repos
            raw.extend(user_repos)

            if n_repos < per_page:
                args = u, page, n_repos, per_page
                logger.debug("Halt user=%r at page=%i; query returned %i repos < per_page=%i.", *args)
                break
            page += 1

        logger.debug("Found %i repo(s) for user %i/%i: '%s'.", n, i, len(user), u)

    logger.info("Found %i repo(s) for %i user(s): %s.", len(raw), len(user), ", ".join(map(repr, user)))

    func = functools.partial(_process_repo, logger=logger, headers=headers, now=now, max_days=max_days)
    with ThreadPoolExecutor(max_workers=8, thread_name_prefix=logger.name) as pool:
        repos = pool.map(func, raw, timeout=300)

    filtered_repos = [r for r in repos if r is not None]
    logger.info("Processed %i/%i matching repos in %s.", len(filtered_repos), len(raw), format_perf_counter(start))

    if not repos:
        click.secho("No repositories found.", fg="green")
        sys.exit(0)

    df = _to_dataframe(filtered_repos, sort)
    pretty = _to_string(df, max_width)
    click.secho(pretty, fg="green")


def _get_headers(logger: logging.Logger) -> dict[str, str] | None:
    if not (path := Path("~/.rics/github-token").expanduser()).is_file():
        logger.debug("Skipping GitHub auth; file not found: '%s'.", path)
        return None

    logger.debug("Found GitHub auth token: '%s'.", path)
    return {
        "Authorization": f"Bearer {path.read_text().strip()}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _process_repo(
    repo: dict[str, Any],
    *,
    logger: logging.Logger,
    headers: dict[str, str] | None,
    now: "pandas.Timestamp",
    max_days: int | None,
) -> "dict[str, str | int | pandas.Timestamp] | None":
    import pandas as pd
    import requests

    if not repo.get("license"):
        logger.debug(f"Skip repo={repo['full_name']!r}: no licence.")
        return None

    url = repo["releases_url"].replace("{/id}", "/latest")
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 404:  # noqa: PLR2004
        logger.debug(f"Skip repo={repo['full_name']!r}: no releases.")
        return None

    release = response.json()
    pushed_at = pd.Timestamp(repo["pushed_at"])
    age = (now - pushed_at).days

    if max_days is not None and age > max_days:
        logger.debug(f"Skip repo={repo['full_name']!r}: {age=} > {max_days=}.")
        return None

    created_at = pd.Timestamp(repo["created_at"])
    return {
        "Repo name": repo["full_name"],
        "Release tag": release["tag_name"],
        _PUSH: pushed_at,
        # "Age [days]": age,
        "Stars": repo["stargazers_count"],
        "Issues": repo["open_issues"],
        "Description": repo["description"],
        "Link": repo["html_url"],
        "License": repo["license"]["spdx_id"],
        "Created": created_at,
        # "Created [days]": (now - created_at).days,
    }


def _to_dataframe(repos: list[dict[str, Any]], sort: str) -> "pandas.DataFrame":
    import pandas as pd

    df = pd.DataFrame.from_records(repos)
    assert (df.dtypes[[_PUSH, "Created"]] == _DATETIME_DTYPE).all()  # noqa: S101

    (sort, ascending) = _SORT_COLUMNS[sort]
    df = df.sort_values(sort, ascending=ascending)
    df = df.set_index("Repo name")

    return df


def _to_string(df: "pandas.DataFrame", max_width: int | None) -> str:
    if max_width is None:
        max_width = _max_width()
    if max_width > 0:
        df["Description"] = df["Description"].str[:max_width]

    pretty = df.to_string(
        max_colwidth=None,
        formatters={_PUSH: "{:%Y-%m-%dT%H:%M:%SZ}".format, "Created": "{:%Y-%m-%d}".format},
    )
    assert isinstance(pretty, str)  # noqa: S101
    return pretty


def _max_width() -> int:
    import os

    try:
        max_width = min(200, max(60, 40 - os.get_terminal_size()[0]))
    except OSError as e:
        from errno import ENOTTY

        if e.errno == ENOTTY:
            max_width = 80
        else:
            raise
    return max_width
