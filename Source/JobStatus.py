import requests
from GitlabToken import gitlab_token

class JobStatus:

    def __init__(self, last_pipeline_id):
        self.gitlab_api_url = "https://gitlab.octafx.com/api/v4/projects/383"
        self.last_pipeline_id = last_pipeline_id
        self.headers = {'Authorization': f'Bearer {gitlab_token}'}
        url = f'{self.gitlab_api_url}/pipelines/{str(self.last_pipeline_id)}'
        jobs_page_1 = requests.get(f'{url}/jobs?per_page=100&page=1', headers=self.headers)
        jobs_page_2 = requests.get(f'{url}/jobs?per_page=100&page=2', headers=self.headers)
        all_jobs = jobs_page_1.json() + jobs_page_2.json()
        self.job_name_and_id = {job["name"]: job["id"] for job in all_jobs}

    def _get_job_status(self, job_name):
        job_id = self.job_name_and_id.get(job_name, None)
        if job_id == None:
            return 0
        job_status = requests.request("GET", url=f"{self.gitlab_api_url}/jobs/{job_id}", \
                                      headers=self.headers).json()
        job_status = job_status["status"]
        job_link = f"https://gitlab.octafx.com/qa/customer-facing-tests/-/jobs/{job_id}"
        emoji_status_dict = {
                             "created": "grey_question",
                             "running": "greenwait",
                             "success": "green-mark",
                             "canceled": "nocontact",
                             "failed": "x",
                             "pending": "double_vertical_bar",
                             "skipped": "stopp"
                            }
        return job_status, job_link, emoji_status_dict

    def _get_disabled_jobs(self):
        raw_disabled_jobs = requests.request("GET", url=f"{self.gitlab_api_url}/variables/SKIPPED_TEST_JOBS",
                                              headers=self.headers).json()
        disabled_jobs = raw_disabled_jobs.get("value", None)
        if disabled_jobs:
            disabled_jobs = disabled_jobs[1 : len(disabled_jobs) - 2].split("|") # убираем первый символ и два последних и разбиваем по |
        return disabled_jobs

    def get_jobs_statuses(self, jobs_to_check_status):
        jobs_info_dict = dict()
        disabled_jobs = self._get_disabled_jobs()
        for job_name in jobs_to_check_status:
            if job_name not in disabled_jobs and self._get_job_status(job_name) != 0:
                job_status, job_link, emoji_status_dict = self._get_job_status(job_name)
                jobs_info_dict[job_name] = {"link": job_link, "status": emoji_status_dict[job_status]}
            else:
                jobs_info_dict[job_name] = {"disabled": True}
        return jobs_info_dict
