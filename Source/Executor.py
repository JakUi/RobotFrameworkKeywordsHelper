import os
import logging
from GetFiles import GetFiles
from KeywordsComponents import KeywordsAndDependencies
from TestComponents import TestsCompositions
from OutputResults import Output
from Jobs import Jobs
from JobStatus import JobStatus
from GetMergeChanges import MergeRequestInfo
from KeywordsCompositions import KeywordsCompositions
from GitlabToken import gitlab_token

# Написать обработчик slash-комманд (команды работают)! 

class Executor:

    def __init__(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        for not_my_logger in logging.Logger.manager.loggerDict:
            logging.getLogger(not_my_logger).disabled = True
        self.Output = Output()

    def _checkout_to_merge_request_branch(self, branch):
        repo_url = f"https://ms-kewyords-helper:{gitlab_token}@gitlab.octafx.com/qa/customer-facing-tests.git"
        dir_exists = os.path.exists("TMP/customer-facing-tests")
        if dir_exists == True:
            os.system(f"(cd TMP/customer-facing-tests && git checkout {branch}) && git pull {repo_url} ||" \
                      f"(cd TMP/customer-facing-tests && git pull {repo_url} && git checkout {branch})")
        else:
            os.system(f"cd TMP && git clone {repo_url} && cd customer-facing-tests && git checkout {branch}")
    
    def _get_info(self, affected_keyword, branch):
        self._checkout_to_merge_request_branch(branch)
        content = GetFiles()
        content.get_all_from_files()
        resource_files, keywords_names = content.resource_files, content.keywords_names
        tests_paths, tests_compositions = content.tests_files, content.tests_names
        KwDpds = KeywordsAndDependencies(keywords_names, resource_files)
        TestCmps = TestsCompositions(tests_paths, tests_compositions, all_keywords=KwDpds.keywords)
        KwDpds.get_all_keywords()
        KwDpds.get_all_dependencies()
        KwDpds.save_keywords_results()
        TestCmps.get_tests_names_and_tags()
        TestCmps.save_tests_results()
        KwCompositions = KeywordsCompositions(affected_keyword=affected_keyword)
        jobs = Jobs()
        if affected_keyword != None:
            keyword_consists_of = KwCompositions.keyword_contains_keywords()
            keyword_included_in = KwCompositions.contains_changeable_keyword()
            affected_tests, affected_setup = KwCompositions.tests_affects()
            jobs.get_jobs_and_tests_info()
            affected_suites = jobs.get_affected_suites(affected_tests, affected_setup)
            affected_jobs = jobs.get_affected_jobs()
            return keyword_consists_of, keyword_included_in, affected_tests, affected_suites, affected_jobs

    def command_flow(self, affected_keyword):
        return self._get_info(affected_keyword, "master")

    def merge_request_flow(self, merge_requests_urls_list, message_timestamp, msg_sender, channel_id):
        mr_info = MergeRequestInfo()
        for merge_request_url in merge_requests_urls_list:
            all_affected_jobs = set()
            affected_keywords_in_mr, affected_suites_in_mr = mr_info.parse_changes_in_merge_request(merge_request_url)
            if affected_keywords_in_mr != "Gitlab API returns error!":
                logging.debug("Keywords which have been affected in this merge request %s" % affected_keywords_in_mr)
                branch, last_pipeline_id = mr_info.get_mr_general_info(merge_request_url)
                logging.debug("Checkout to MR's branch %s" %(branch))
                self._checkout_to_merge_request_branch(branch)
                logging.debug("\\------------------------------------------------------------------")
                JStatus = JobStatus(last_pipeline_id)
                self._get_info(None, branch)
                for keyword in affected_keywords_in_mr:
                    KwCompositions = KeywordsCompositions(affected_keyword=keyword)
                    logging.debug("Now I'm working with keyword:'%s'" % (keyword))
                    KwCompositions.find_keyword_childs()
                    affected_tests, affected_setup = KwCompositions.tests_affects()
                    jobs = Jobs()
                    jobs.get_jobs_and_tests_info()
                    jobs.get_affected_suites(affected_tests, affected_setup)
                    affected_jobs = jobs.get_affected_jobs()
                    for affected_job in affected_jobs:
                        all_affected_jobs.add(affected_job)
                report_messages_message_dict = {"affectedJobs": all_affected_jobs}
                jobs_info = JStatus.get_jobs_statuses(all_affected_jobs)
                self.Output.post_results_to_thread_in_slack(channel_id, report_messages_message_dict, message_timestamp, msg_sender, jobs_info)
            else:
                report_messages_message_dict = {"gitlabError": all_affected_jobs}
                self.Output.post_results_to_thread_in_slack(channel_id, report_messages_message_dict, message_timestamp, msg_sender)
