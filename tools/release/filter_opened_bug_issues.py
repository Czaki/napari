import argparse
from datetime import datetime

from tqdm import tqdm

from release_utils import (
    GH_REPO,
    GH_USER,
    get_common_ancestor,
    get_github,
    get_milestone,
    get_repo,
    setup_cache,
)

parser = argparse.ArgumentParser(usage=__doc__)
parser.add_argument('from_commit', help='The starting tag.')
parser.add_argument('to_commit', help='The head branch.')
parser.add_argument(
    "--milestone",
    help="if present then filter issues with a given milestone",
    default=None,
    type=str,
)

args = parser.parse_args()

setup_cache()

repository = get_repo()

milestone = get_milestone(args.milestone)

common_ancestor = get_common_ancestor(args.from_commit, args.to_commit)
remote_commit = repository.get_commit(common_ancestor.hexsha)
previous_tag_date = datetime.strptime(
    remote_commit.last_modified, '%a, %d %b %Y %H:%M:%S %Z'
)

probably_solved = repository.get_label("probably solved")

issue_list = []

for issue in tqdm(
    get_github().search_issues(
        f'repo:{GH_USER}/{GH_REPO} '
        "is:issue "
        "is:open "
        "label:bug "
        f'created:>{previous_tag_date.isoformat()} '
        'sort:updated-desc'
    ),
    desc='issues...',
):
    if probably_solved in issue.labels:
        continue
    if issue.milestone != milestone:
        continue

    issue_list.append(issue)

print(f"Found {len(issue_list)} issues")

if milestone:
    print(f"## Opened Issues with bug label and milestone {milestone.title}:")
else:
    print("## Opened Issues with bug label and no milestone:")

for issue in issue_list:
    print(f" * [ ] #{issue.number}")
