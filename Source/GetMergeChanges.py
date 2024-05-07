import os
import requests
import logging
from requests.exceptions import HTTPError
from GitlabToken import gitlab_token

class MergeRequestInfo:

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.gitlab_api_url = "https://gitlab.octafx.com/api/v4/projects"
        try:
            self.gitlab_token = os.environ["gitlab_token"]
        except:
            self.gitlab_token = gitlab_token
        self.affected_keywords_names_set = set()
        self.affected_suites_paths_set = set()

    def _gitlab_api_request(self, merge_request_url):
        payload={}
        headers = {'Authorization': f'Bearer {self.gitlab_token}'}
        try:
            response = requests.request("GET", merge_request_url, headers=headers, data=payload)
            response.raise_for_status()
            return response.json()
        except HTTPError as http_err:
            logging.error(f'HTTP error occurred: {http_err}')
            return "Error in response!"
        except Exception as err:
            logging.error(f'Other error occurred: {err}')
            return "Error in response!"

    def get_mr_general_info(self, merge_request_url):
        logging.debug("Get merge request's branch")
        resp = self._gitlab_api_request(merge_request_url)
        branch = resp["source_branch"]
        last_pipeline_id = resp["head_pipeline"]["id"]
        return branch, last_pipeline_id

    def parse_changes_in_merge_request(self, merge_request_url):
        merge_request_branch, last_pipeline_id = self.get_mr_general_info(merge_request_url)
        url = self.gitlab_api_url + "/383/repository/compare?from=master&to=" + merge_request_branch
        logging.debug("Get merge request's changes body")
        merge_request_body = self._gitlab_api_request(merge_request_url=url)
        if merge_request_body != "Error in response!":
            commits_count = len(merge_request_body["diffs"])
            for i in range(0, commits_count):
                changed = merge_request_body["diffs"][i]
                if changed["new_path"].startswith("Resources"):
                    self._get_changes(changed["diff"])
                elif changed["new_path"].startswith("Tests"):
                    self.affected_suites_paths_set.add(changed["new_path"])
            return self.affected_keywords_names_set, self.affected_suites_paths_set
        else:
            return "Gitlab API returns error!", None

    def _are_there_any_changes(self, by_lines, line_number, total_lines_in_diff, line_with_name):
        for n in range(line_number, total_lines_in_diff):
            if by_lines[n].startswith("+  ") or by_lines[n].startswith("-  "):
                self.affected_keywords_names_set.add(line_with_name)
                break
            elif by_lines[n] == " \n" or n == (total_lines_in_diff - 1) or by_lines[n + 1].startswith("@@"):
                break
            elif by_lines[n].startswith("-") or by_lines[n].startswith("+"):
                break

    def _get_changes(self, changed):
        line_with_name = None
        by_lines = changed.split("\n")
        total_lines_in_diff = len(by_lines)
        kw_name_not_starts_with = ("$", "@", "*", "Library", "Resource")
        for line_number in range(0, total_lines_in_diff):
            if by_lines[line_number].startswith("@@"): # Keyword exist but hidden in @@ @@
                line_with_name = by_lines[line_number]
                counter = line_number + 1
                keyword_name_found = False
                while by_lines[counter] != " ":
                    if len(by_lines[counter]) == 0:
                        break
                    if by_lines[counter].startswith(" ") and not by_lines[counter].startswith("    "):
                        logging.debug("Keyword %s exist, was changed",
                                       by_lines[line_number][by_lines[line_number].rfind("@@") + 3 : ])
                        line_with_name = by_lines[counter][1 : ]
                        keyword_name_found = True
                    counter += 1
                if keyword_name_found == False:
                    line_with_name = by_lines[line_number][by_lines[line_number].rfind("@@") + 3 : ]
                    logging.debug("Keyword %s exist but hidden in @@ @@", line_with_name)
                if line_with_name.replace(" ", "").startswith(kw_name_not_starts_with):
                    continue
                else:
                    self._are_there_any_changes(by_lines, line_number, total_lines_in_diff, line_with_name)
                    line_number = counter
            elif by_lines[line_number].startswith(" ") and not by_lines[line_number].startswith("  ") and \
            by_lines[line_number] != " ": # Keywords exist, was changed
                line_with_name = by_lines[line_number][1 : ]
                if  line_with_name.replace(" ", "").startswith(kw_name_not_starts_with):
                    continue
                else:
                    self._are_there_any_changes(by_lines, line_number, total_lines_in_diff, line_with_name)
            elif by_lines[line_number].startswith("+") and not by_lines[line_number].startswith("+  ") and not \
            by_lines[line_number].startswith("+\n") and by_lines[line_number] != "+": # New keyword has been added
                logging.debug("New keyword has been added")
                if  by_lines[line_number][1 : ].replace(" ", "").startswith(kw_name_not_starts_with):
                    continue
                else:
                    self.affected_keywords_names_set.add(by_lines[line_number][1 : ])
            elif by_lines[line_number].startswith("-") and not by_lines[line_number].startswith("-  ") and not \
            by_lines[line_number].startswith("-\n") and by_lines[line_number] != "-": # Keyword has been removed
                if  by_lines[line_number][1 : ].replace(" ", "").startswith(kw_name_not_starts_with):
                    continue
                else:
                    self.affected_keywords_names_set.add(by_lines[line_number][1 : ])
                    logging.debug("Keyword %s has been removed", by_lines[line_number][1 : ])
