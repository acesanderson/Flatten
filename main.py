"""
Currently grabs all .py files from the main branch.
Future functionality:
- do the same from project directory
- generate a tree of the zipfile (and project directory) as part of llm context
- allow customizing branch + file extension

NOTE: Path.walk() would be handy way to get all file contents for a repo
"""

import requests
import zipfile
from io import BytesIO
import argparse
import os

token = os.getenv("GITHUB_TOKEN")  # Token expires end of April 2025
headers = {"Authorization": f"token {token}"}

# Generate examples for testing

repos = [
    {"owner": "acesanderson", "repo": "Kramer", "branch": "main"},
    {"owner": "acesanderson", "repo": "Chain", "branch": "main"},
    {"owner": "acesanderson", "repo": "Leviathan", "branch": "master"},
    {"owner": "acesanderson", "repo": "Mentor", "branch": "agentic"},
    {"owner": "acesanderson", "repo": "Daisy", "branch": "main"},
    {"owner": "acesanderson", "repo": "twig", "branch": "main"},
    {"owner": "acesanderson", "repo": "ask", "branch": "master"},
]


# Our functions
def parse_user_inputted_url(base_url: str) -> str:
    """
    Take base urls of format "https://github.com/acesanderson/twig" and convert to repo_url.
    """
    owner = base_url.split("/")[-2]
    repo = base_url.split("/")[-1]
    branch = "main"
    repo_url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
    return repo_url


def grab_repo(repo_url: str) -> str:
    response = requests.get(repo_url, headers=headers)
    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch repository: {response.status_code}")
    # Step 2: Load the zip file into memory
    zip_file = BytesIO(response.content)
    # Step 3: Extract and work with the contents of the zip file
    output = ""
    with zipfile.ZipFile(zip_file, "r") as z:
        file_list = z.namelist()
        for file in file_list:
            if file.endswith(".py"):
                with z.open(file) as f:
                    content = f.read()
                    output += "-------------------------------------------\n"
                    output += f"Content of {file}:\n"
                    output += "-------------------------------------------\n"
                    output += (
                        content.decode("utf-8") + "\n"
                    )  # Assuming the file is text and UTF-8 encoded
        return output


def grab_repos():
    output = []
    for repository in repos:
        try:
            match repository:  # Experimenting with a dictionary pattern with /match/case
                case {"owner": owner, "repo": repo, "branch": branch}:
                    url = (
                        f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
                    )
                    output.append(grab_repo(url))
        except Exception as e:
            print(f"Error fetching {repository['repo']}: {e}")
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", type=str, nargs="?", help="The repository to fetch")
    args = parser.parse_args()
    if args.base_url:
        repo_url = parse_user_inputted_url(args.base_url)
        output = grab_repo(repo_url)
        print(output)
    else:
        print("Please provide a repository URL.")


if __name__ == "__main__":
    # main()
    output = grab_repos()
    print(output[1])
