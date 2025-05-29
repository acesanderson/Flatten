from io import BytesIO
import argparse, os, sys, zipfile, requests
from pathlib import Path
import xml.dom.minidom as md
import xml.etree.ElementTree as ET
from typing import TypeAlias


token = os.getenv("GITHUB_TOKEN")  # Token expires end of April 2025
headers = {"Authorization": f"token {token}"}
XMLString: TypeAlias = str  # Type alias for XML string

# Generate examples for testing

repos = [
    # {"owner": "acesanderson", "repo": "Kramer", "branch": "main"},
    # {"owner": "acesanderson", "repo": "Chain", "branch": "main"},
    # {"owner": "acesanderson", "repo": "Leviathan", "branch": "master"},
    # {"owner": "acesanderson", "repo": "Mentor", "branch": "agentic"},
    # {"owner": "acesanderson", "repo": "Curator", "branch": "v2"},
    # {"owner": "acesanderson", "repo": "Daisy", "branch": "main"},
    # {"owner": "acesanderson", "repo": "twig", "branch": "main"},
    # {"owner": "acesanderson", "repo": "ask", "branch": "master"},
    {"owner": "acesanderson", "repo": "Haddock", "branch": "main"},
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
    """
    Analyze a GitHub repo.
    """
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
            if file.endswith(".py") or file.endswith(".lua"):
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


def create_directory_xml(current_working_directory: Path) -> ET.Element:
    """
    Create an XML representation of the directory structure,
    including Python files (*.py) and Markdown files (*.md),
    and lua (*.lua) while excluding patterns similar to gitignore.
    """
    directory_tree = ET.Element("directory_tree")
    directory = ET.SubElement(
        directory_tree, "directory", name=current_working_directory.name
    )

    # Patterns to exclude (similar to .gitignore)
    exclude_dirs = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        "*.egg-info",
        ".DS_Store",
        ".venv",
        "venv",
        ".env",
        "cache",
        "*.pyc",
    ]

    for dirpath, dirnames, filenames in os.walk(current_working_directory):
        # Skip excluded directories
        basename = os.path.basename(dirpath)

        # Check if the current directory should be excluded
        should_exclude = False
        for pattern in exclude_dirs:
            if pattern.startswith("*."):
                # Handle wildcard patterns for extensions
                if basename.endswith(pattern[1:]):
                    should_exclude = True
                    break
            elif pattern == basename or pattern in dirpath:
                should_exclude = True
                break

        if should_exclude:
            continue

        # Also modify dirnames in-place to prevent os.walk from entering excluded dirs
        i = 0
        while i < len(dirnames):
            dirname = dirnames[i]
            exclude_this_dir = False
            for pattern in exclude_dirs:
                if pattern.startswith("*."):
                    # Handle wildcard patterns for extensions
                    if dirname.endswith(pattern[1:]):
                        exclude_this_dir = True
                        break
                elif pattern == dirname:
                    exclude_this_dir = True
                    break

            if exclude_this_dir:
                dirnames.pop(i)
            else:
                i += 1

        # Create subdirectory in XML
        subdir = ET.SubElement(directory, "directory", name=basename)

        # Add files to the XML structure, excluding unwanted file types
        for filename in filenames:
            # Skip excluded file patterns
            skip_file = False
            for pattern in exclude_dirs:
                if pattern.startswith("*."):
                    if filename.endswith(pattern[1:]):
                        skip_file = True
                        break
                elif pattern == filename:
                    skip_file = True
                    break

            if skip_file:
                continue

            # Include only files with desired extensions
            if filename.endswith((".py", ".md", ".lua")):  # Include both .py and .md
                file_path = os.path.join(dirpath, filename)
                file_element = ET.SubElement(
                    subdir, "file", name=filename, path=file_path
                )

    return directory_tree


def get_files(cwd: Path) -> list[Path]:
    """
    Get all of the python and markdown files from the project directories,
    excluding patterns similar to gitignore.
    """
    # Patterns to exclude (similar to .gitignore)
    exclude_patterns = [
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        "*.egg-info",
        ".DS_Store",
        ".venv",
        "venv",
        ".env",
        "cache",
        "*.pyc",
    ]

    files = []
    for dirpath, dirnames, filenames in os.walk(cwd):
        # Skip excluded directories
        path_str = str(dirpath)
        should_skip = False
        for pattern in exclude_patterns:
            if pattern.startswith("*."):
                # Skip directories ending with pattern
                if path_str.endswith(pattern[1:]):
                    should_skip = True
                    break
            elif pattern in path_str:
                should_skip = True
                break

        if should_skip:
            continue

        # Process files in non-excluded directories
        for filename in filenames:
            # Skip excluded file patterns
            skip_file = False
            for pattern in exclude_patterns:
                if pattern.startswith("*."):
                    if filename.endswith(pattern[1:]):
                        skip_file = True
                        break
                elif pattern == filename:
                    skip_file = True
                    break

            if skip_file:
                continue

            # Include only files with desired extensions
            if filename.endswith((".py", ".md")):
                file_path = os.path.join(dirpath, filename)
                files.append(Path(file_path))

    return files


def get_file_contents(files: list[Path]) -> ET.Element:
    """
    Grab text from all .py files, wrapping them in xml tags with proper CDATA sections.
    Returns an Element, not a string.
    """
    root = ET.Element("file_contents")

    # First create the basic structure with ElementTree
    file_elements = []
    for file in files:
        file_elem = ET.SubElement(root, "file", path=str(file))
        file_elements.append((file, file_elem))

    # Convert to string and parse with minidom to add CDATA
    xml_str = ET.tostring(root, encoding="unicode")
    dom = md.parseString(xml_str)

    # Add CDATA sections to each file element
    for i, (file, _) in enumerate(file_elements):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
                file_element = dom.getElementsByTagName("file")[i]
                cdata = dom.createCDATASection(content)
                file_element.appendChild(cdata)
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    # Convert back to ElementTree
    new_root = ET.fromstring(dom.toxml())
    return new_root


def package_project_directory(directory: Path) -> XMLString:
    """
    Wrapper function for grabbing project context from local filesystem.
    If user enters '.', assume you are in the base of a project directory, walk the entire structure, and return the package.
    This is the <project> element in the XML.
    """
    # Create the root project element
    root = ET.Element("project", name=directory.name)

    # Get directory structure
    dir_tree = create_directory_xml(directory)
    root.append(dir_tree)

    # Get file contents
    files = get_files(directory)
    file_contents = get_file_contents(files)
    root.append(file_contents)

    # Convert to string with proper formatting
    rough_string = ET.tostring(root, encoding="unicode")

    # Use minidom to prettify and ensure proper CDATA handling
    dom = md.parseString(rough_string)
    pretty_xml = dom.toprettyxml(indent="  ")

    return pretty_xml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url", type=str, nargs="?", help="The repository to fetch")
    args = parser.parse_args()
    url = args.base_url
    if url == ".":
        project_directory_context = package_project_directory(Path.cwd())
        print(project_directory_context)
        sys.exit()
    repo_url = parse_user_inputted_url(args.base_url)
    output = grab_repo(repo_url)
    print(output)


if __name__ == "__main__":
    main()
