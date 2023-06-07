import os
import re
import sys
from contextlib import contextmanager

from github import Github

pr_num_pattern = re.compile(r'\(#(\d+)\)(?:$|\n)')


@contextmanager
def short_cache(new_time):
    """
    context manager for change cache time in requests_cache
    """
    try:
        import requests_cache
    except ImportError:
        yield
        return

    import requests

    if requests_cache.get_cache() is None:
        yield
        return
    session = requests.Session()
    old_time = session.expire_after
    session.expire_after = new_time
    try:
        yield
    finally:
        session.expire_after = old_time


def setup_cache(timeout=3600):
    """
    setup cache for speedup execution and reduce number of requests to GitHub API
    by default cache will expire after 1h (3600s)
    """
    try:
        import requests_cache
    except ImportError:
        print("requests_cache not installed", file=sys.stderr)
        return

    """setup cache for requests"""
    requests_cache.install_cache(
        'github_cache', backend='sqlite', expire_after=timeout
    )


GH = "https://github.com"
GH_USER = 'napari'
GH_REPO = 'napari'
GH_TOKEN = os.environ.get('GH_TOKEN')
if GH_TOKEN is None:
    raise RuntimeError(
        "It is necessary that the environment variable `GH_TOKEN` "
        "be set to avoid running into problems with rate limiting. "
        "One can be acquired at https://github.com/settings/tokens.\n\n"
        "You do not need to select any permission boxes while generating "
        "the token."
    )

_G = None


def get_github():
    global _G
    if _G is None:
        _G = Github(GH_TOKEN)
    return _G


def get_repo():
    g = get_github()
    return g.get_repo(f'{GH_USER}/{GH_REPO}')


def get_local_repo():
    """
    get local repository
    """
    from pathlib import Path

    from git import Repo

    return Repo(Path(__file__).parent.parent.parent)


def get_common_ancestor(commit1, commit2):
    """
    find common ancestor for two commits
    """
    local_repo = get_local_repo()
    return local_repo.merge_base(commit1, commit2)[0]


def get_commits_to_ancestor(ancestor, rev="main"):
    local_repo = get_local_repo()
    yield from local_repo.iter_commits(f'{ancestor.hexsha}..{rev}')


def get_commit_counts_from_ancestor(release, rev="main"):
    """
    get number of commits from ancestor to release
    """
    ancestor = get_common_ancestor(release, rev)
    return sum(
        pr_num_pattern.search(c.message) is not None
        for c in get_commits_to_ancestor(ancestor, rev)
    )