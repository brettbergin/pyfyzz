#!/usr/bin/env python3

import os
import ast
import base64

from git import Repo, GitCommandError
from github import Github

from .models.orm_models import PackageTopology, FuzzResults
from .patcher import PyFyzzCodePatcher


class GithubForPyFyzz(PyFyzzCodePatcher):

    def __init__(self, logger, access_token: str) -> None:
        super().__init__(logger)

        if not access_token or not isinstance(access_token, str):
            self.logger.log("error", "Access token not provided or is invalid.")
            raise TypeError(
                "Access token not provided. Cannot create PyGithub integration."
            )

        self.logger = logger
        self.access_token = access_token
        self.github = Github(self.access_token)

        self.db = None

        self.repo_url = None
        self.git_repo = None
        self.repo = None

        self.repo_str = None
        self.repo_owner = None
        self.repo_name = None

    def _set_github_repo(self):
        """
        Sets the repository using the provided repo URL.
        """
        self.logger.log("info", "[+] Initializing the GitHub repository.")

        if not isinstance(self.repo_url, str):
            self.logger.log("error", "[-] Repo URL is not a string.")
            raise TypeError("Repo URL is not a string.")

        parts = self.repo_url.strip().split("/")

        self.repo_owner = parts[-2]
        self.repo_name = parts[-1]
        self.repo_str = f"{self.repo_owner}/{self.repo_name}"

        try:
            self.repo = self.github.get_repo(self.repo_str)
            self.logger.log("info", f"[+] Successfully set repository: {self.repo_str}")
            return True

        except Exception as err:
            self.logger.log(
                "error",
                f"[-] Unable to construct repo with: {self.repo_str} | Error: {err}",
            )
            return False

    def _commit_and_push_changes(
        self, commit_message: str, branch_name: str, and_push: bool = False
    ):
        """
        Commits and pushes changes to the specified branch.
        """
        self.logger.log(
            "info",
            f"[+] Committing changes to branch '{branch_name}' with message '{commit_message}'.",
        )

        if not isinstance(self.git_repo, Repo):
            self.logger.log(
                "error",
                f"[-] self.git_repo is not a valid git.Repo object. Received: {type(self.git_repo)}. Unable to commit and push changes.",
            )
            return False

        try:
            self.git_repo.git.add(update=True)
            self.git_repo.index.commit(commit_message)

            if and_push:
                self.logger.log(
                    "info",
                    f"[+] Attempting to push changes to remote branch: '{branch_name}'",
                )

                origin = self.git_repo.remote(name="origin")
                origin.push(branch_name)

                self.logger.log(
                    "info",
                    f"[+] Changes committed and pushed to remote branch '{branch_name}'",
                )
                return True

            self.logger.log("info", f"[+] Changes committed to branch '{branch_name}'")
            return False

        except GitCommandError as e:
            self.logger.log("error", f"[-] Failed to push changes: {str(e)}")
            return False

    def _make_pull_request(self, branch_name: str, pr_title: str, pr_body: str):
        """
        Creates a pull request from the specified branch.
        """
        self.logger.log(
            "info",
            f"[+] Creating pull request from branch '{branch_name}' with title '{pr_title[0:20]}... (trunc'd)'.",
        )

        try:
            pr = self.repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=self.repo.default_branch,
            )

            self.logger.log(
                "info", f"[+] New Pull request successfully created: {pr.html_url}"
            )
            return True

        except Exception as e:
            self.logger.log("error", f"[-] Error creating new pull request: {str(e)}")
            return False

    def _pull_latest_changes(self, clone_path):
        """
        If we can't clone a repo, let's pull the latest code.
        """
        self.logger.log(
            "info",
            f"[+] Attempting `git pull` on the provided folder path: {clone_path}.",
        )

        try:
            # Open the repository at the clone_path
            repo = Repo(clone_path)

            # Check the current branch
            current_branch = repo.active_branch
            self.logger.log(
                "info", f"[+] Currently running on branch: {current_branch}"
            )

            # Check if the current branch is tracking a remote branch
            if current_branch.tracking_branch() is None:
                self.logger.log(
                    "error",
                    f"[-] The branch {current_branch} are not currently tracked in any remote branch.",
                )
                return False

            # Get the remote
            origin = repo.remotes.origin

            # Attempt to pull the latest changes
            self.logger.log(
                "info", "[+] Attempting to pull the latest changes from origin."
            )
            pull_result = origin.pull()

            # Check the pull result for success or merge conflicts
            for info in pull_result:
                if info.flags & info.HEAD_UPTODATE:
                    self.logger.log(
                        "info", f"[+] Branch '{current_branch}' is already up to date."
                    )
                elif info.flags & info.FAST_FORWARD:
                    self.logger.log(
                        "info",
                        f"[+] Successfully pulled changes into '{current_branch}' (fast-forward).",
                    )
                else:
                    self.logger.log(
                        "info", f"[!] Unknown merge result. See: {info.summary}"
                    )

            return True

        except GitCommandError as e:
            self.logger.log(
                "error",
                f"[-] An git related error occurred during `git pull`: {str(e)}",
            )
            return False

        except Exception as e:
            self.logger.log("error", f"[-] An Unexpected error occurred: {str(e)}")
            return False

    def _fetch_db_resources(self, package: str, method: str):
        """
        Take the package_name and method_name and fetch the
        corresponding fuzz result database row from pyfyzz db.
        """

        try:
            fuzz_result = (
                self.db.session.query(FuzzResults)
                .filter(
                    FuzzResults.package_name == package,
                    FuzzResults.method_name == method,
                )
                .first()
            )

            if fuzz_result is None:
                self.logger.log(
                    "error",
                    f"[-] No database entry found for package: {package}, method: {method}",
                )
                return None
            return fuzz_result

        except Exception as err:
            self.logger.log(
                "error",
                f"[-] Unable to fetch pyfyzz db resources for pull request generation. Error: {err}",
            )
            return None

    def _create_file_content(self, folder, fuzz_res, package, method, new_code):
        """
        Take the encoded source and generate updated file content that can be written to file.
        """
        try:
            original_code = base64.b64decode(fuzz_res.encoded_source).decode("utf-8")
            file_path = self._find_file_with_code(
                folder_path=folder, original_code=original_code
            )

            if file_path is None:
                self.logger.log(
                    "error",
                    f"[-] File not found for method {method} in package {package}. Unable to make improvements.",
                )
                return (None, None)

            if not os.path.exists(file_path):
                self.logger.log(
                    "error",
                    f"[-] File doesn't exist for method {method} in package {package}. Unable to make improvements.",
                )
                return (None, None)

            with open(file_path, "r") as f:
                file_content = f.read()

            indented_new_code = self._ensure_indentation_replacement(
                original_code, new_code
            )
            updated_content = file_content.replace(original_code, indented_new_code)
            return (file_path, updated_content)

        except Exception as e:
            self.logger.log(
                "error",
                f"[-] Cannot generate updated file content for {method} in {package}: {str(e)}",
            )
            return (None, None)

    def _write_file(self, f, c):
        """
        Write the updated code to file.
        """
        try:
            self.logger.log("info", "[+] Attempting to write improvement to file.")
            tree = ast.parse(c)
            self._write_ast_to_file(tree, f)

            # Format the code with black to resolve any ast formatting concerns.
            self._format_with_black(dir_path=f)
            return True

        except Exception as err:
            self.logger.log(
                "error", f"[-] Cannot write updated AST content to file. Error: {err}"
            )
            return False

    def _resolve_file_changes(self):
        """
        Commit and optionally push the improvements to the git repository.
        """
        try:

            self.logger.log(
                "info", "[+] Attempting commit of code improvements to repository."
            )
            self._commit_and_push_changes(
                commit_message="automated improvements",
                branch_name="improvements",
                and_push=False,
            )
            return True

        except Exception as err:
            self.logger.log("error", f"[-] Cannot commit changes to repo. Error: {err}")
            return False

    def _create_new_merge(self):
        """
        Attempt to create a pull request with the locally created changes.
        """
        try:
            self.logger.log(
                "info", "[+] Attempting pull request generation from code changes."
            )
            self._make_pull_request(
                branch_name="improvements",
                pr_title="added improvements",
                pr_body="This PR attempts to improve the way arguments are being handled.",
            )
            return True

        except Exception as err:
            self.logger.log(
                "error", f"[-] Unable to generate new pull request. Error: {err}"
            )
            return False

    def init_repo_from_url(self, repo_url: str):
        """
        Initializes the repository from a given URL.
        """
        if not isinstance(repo_url, str):
            self.logger.log("error", f"[-] Invalid repository URL provided. {repo_url}")
            raise ValueError(f"Invalid Github Repository URL Provided. {repo_url}")

        self.logger.log("info", f"[+] Initializing repo via Github URL: {repo_url}")

        self.repo_url = repo_url
        self._set_github_repo()

        return True

    def create_repo_clone(
        self, repo_url: str, repo_name: str, clone_path: str, new_branch_name: str
    ):
        """
        Clones a repository to the specified local path and creates a new branch.
        """
        if (
            not isinstance(repo_url, str)
            or not isinstance(repo_name, str)
            or not isinstance(clone_path, str)
            or not isinstance(new_branch_name, str)
        ):
            self.logger.log(
                "error",
                "[-] Invalid parameters: repo_url, repo_name, clone_path, and new_branch_name must be strings.",
            )
            return False

        self.logger.log(
            "info",
            f"[+] Cloning repository {repo_name} to {clone_path} and creating new branch '{new_branch_name}'",
        )

        try:
            # If the repository already exists in the specified path, remove it
            if os.path.exists(clone_path):
                self.logger.log(
                    "info", f"[+] Repo directory exists at location: {clone_path}."
                )
                self._pull_latest_changes(clone_path=clone_path)
                self.git_repo = Repo(clone_path)

            else:
                # Clone the repository
                self.git_repo = Repo.clone_from(repo_url, clone_path)
                self.logger.log(
                    "info",
                    f"[+] Successfully cloned repository {repo_url} to {clone_path}",
                )

        except Exception as err:
            self.logger.log(
                "error",
                f"[-] Attempting a `git pull` on {clone_path} failed. Error: {err}",
            )
            return False

        try:
            # Ensure the repository is not in a detached HEAD state
            if self.git_repo.head.is_valid():
                self.logger.log(
                    "info", "[+] Tested repository. Found a valid HEAD, after cloning."
                )
            else:
                self.logger.log(
                    "error",
                    "[-] HEAD found as not valid. Repository might be empty or not initialized.",
                )

            default_branch = self.git_repo.active_branch.name
            self.logger.log(
                "info", f"[+] Currently running on branch: {default_branch}"
            )

            # Create new branch and ensure checkout
            if new_branch_name not in self.git_repo.branches:
                new_branch = self.git_repo.create_head(new_branch_name)
                self.logger.log("info", f"[+] Created a new branch '{new_branch_name}'")
            else:
                self.logger.log(
                    "info",
                    f"[+] Branch '{new_branch_name}' already exists. No need to create new branch.",
                )
                new_branch = self.git_repo.branches[new_branch_name]

            new_branch.checkout(force=True)
            self.logger.log(
                "info",
                f"[+] Checking out branch '{new_branch_name}' and switching to this branch.",
            )

            # Confirm the branch switch
            current_branch = self.git_repo.active_branch.name
            if current_branch == new_branch_name:
                self.logger.log(
                    "info",
                    f"[+] Successfully switched to new branch: {new_branch_name}",
                )
            else:
                self.logger.log(
                    "error",
                    f"[-] Failed to switch to branch {new_branch_name}, currently on {current_branch}",
                )

        except Exception as e:
            self.logger.log(
                "error", f"[-] Error during cloning and branch creation: {e}"
            )
            return False

        return True

    def make_improvements(
        self, folder_path, package_name, method_name, new_method_code
    ):
        """
        Fetches and replaces method definition.
        """

        self.logger.log(
            "info",
            f"[+] Applying code enhancements to '{method_name}' within package '{package_name}'.",
        )

        fuzz_result = self._fetch_db_resources(package_name, method_name)

        if not fuzz_result:
            self.logger.log(
                "error",
                f"[-] No fuzz result record found in database for package/method combo.",
            )
            return False

        file_path, updated_content = self._create_file_content(
            folder=folder_path,
            fuzz_res=fuzz_result,
            package=package_name,
            method=method_name,
            new_code=new_method_code,
        )

        if not file_path or not updated_content:
            self.logger.log(
                "error",
                f"[-] File path {file_path} or file content {updated_content} invalid in some way. ",
            )
            return False

        self._write_file(f=file_path, c=updated_content)
        self._resolve_file_changes()
        self._create_new_merge()

        self.logger.log(
            "info", "[+] Attempting to apply codebase improvements is complete."
        )
