import json
import re
import logging


class Jobs:
    
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)
        self.jobs_components, self.tests_jobs = dict(), dict()
        self.jobs_files = ["TMP/customer-facing-tests/Includes/robot/customer-facing-tests-ofx.yml"]
        self.path_to_tests_components_file = "Results/AllTests.json"
        self.affected_suites, self.affected_jobs = set(), set()
        self.suites_composition = None

    def _get_file_content(self, path_to_file):
        with open(path_to_file, "r") as file:
            file_content = file.read().split("\n")
        return file_content

    def _get_test_job(self, file_content):
        path_to_tests, test_tag = None, None
        for l in file_content:
            path_and_tag = dict()
            if not l.startswith(" ") and l != "":
                job_name = l[ : l.rfind(":")]
            elif l.count("make") and l.count("p=") or (l.count("make") and l.count("Tests")):
                row_path = re.search("p=Tests\/[a-zA-Z0-9\/]*.robot|p=Tests\/[a-zA-Z0-9\/]*|p=Tests", l)
                if  l.count("i="):
                    row_tag = re.search("i=[a-zA-Z0-9\-]*", l)
                else:
                    row_tag = None
                if row_path != None:
                    path_to_tests = row_path.group(0)
                    path_to_tests = path_to_tests[path_to_tests.find("=") + 1 :]
                if row_tag != None:
                    test_tag = row_tag.group(0)
                    test_tag = test_tag[test_tag.find("=") + 1 :]
                else:
                    test_tag = ""
                path_and_tag["tag"] = test_tag
                path_and_tag["path"] = path_to_tests
                self.jobs_components[job_name] = path_and_tag
            elif l.count("make") and l.count("p=") == 0 and l.count("i="):
                row_tag = re.search("i=[a-zA-Z0-9\-]*", l)
                test_tag = row_tag.group(0)
                test_tag = test_tag[test_tag.find("=") + 1 :]
                path_to_tests = "Tests"
                path_and_tag["tag"] = test_tag
                path_and_tag["path"] = path_to_tests
                self.jobs_components[job_name] = path_and_tag

    def _save_found_jobs(self):
        with open("Results/Jobs.json", "w") as file:
            file.write(json.dumps(self.jobs_components, indent=2))

    def _get_content_from_job_files(self, include_files):
        for file in include_files:
            file_content = self._get_file_content(file)
            self._get_test_job(file_content)

    def get_jobs_and_tests_info(self):
        self._get_content_from_job_files(include_files=self.jobs_files)
        self._save_found_jobs()

    def get_affected_suites(self, affected_tests, affected_setup):
        with open(self.path_to_tests_components_file, "r") as file:
            self.suites_composition = json.load(file)
        for path in affected_setup:
            if path in self.suites_composition.keys():
                self.affected_suites.add(path.replace("TMP/customer-facing-tests/", ""))
        for test in affected_tests:
            for path_to_suite, suite_components in self.suites_composition.items():
                if test in suite_components["Tests"]:
                    self.affected_suites.add(path_to_suite)
        text_affected_suites = "Affected suites:\n ```%s```" % self.affected_suites
        logging.debug(text_affected_suites)
        return self.affected_suites

    def get_affected_jobs(self):
        for path_to_affected_suite in self.affected_suites:
            if not path_to_affected_suite.startswith("TMP/"):
                suite_tags = self.suites_composition[f"TMP/customer-facing-tests/{path_to_affected_suite}"]["Tags"]
            else:
                suite_tags = self.suites_composition[path_to_affected_suite]["Tags"]
            for job_name, job_composition in self.jobs_components.items():
                if suite_tags:
                    if path_to_affected_suite.count(job_composition["path"]) and job_composition["tag"] in suite_tags: # в джобе есть тег и путь к папке
                        self.affected_jobs.add(job_name)
                    elif job_composition["tag"] in suite_tags and job_composition["path"] == "Tests": # есть только тег (в тестах нет тега)
                        self.affected_jobs.add(job_name)
                elif job_composition["path"] == path_to_affected_suite: # в джобе нет тега (только путь к тестам)
                    self.affected_jobs.add(job_name)
        text_affected_jobs = "Jobs which has been affected by edits in this keyword:\n ```%s```" % self.affected_jobs
        logging.debug(text_affected_jobs)
        logging.debug("\\------------------------------------------------------------------")
        return self.affected_jobs
