import json
import logging
from slack_sdk import WebClient
from SlackToken import slack_token


class Output():

    def __init__(self) -> None:
        # self.channel_id = "CP1RYELKF" # Канал для тестов
        self.slack_token = slack_token
        self.client = WebClient(token=self.slack_token)
        logging.basicConfig(level=logging.DEBUG)
 
    def _create_plain_text_message_block(self, block_name, text):
        block = {
                  "type": "section",
                  "block_id": block_name,
                  "text": {
                    "type": "mrkdwn",
                    "text": text
                  }
                }
        return block

    def _create_list_message_block(self, jobs_info_dict):
        all_affected_jobs_block = []
        for job, info in jobs_info_dict.items():
            if info.get("disabled", None) != True:
                list_block = {
                               "type": "rich_text_section",
                               "elements": [
                                 {
                                   "type": "link",
                                   "url": info["link"],
                                   "text": job,
                                   "style": {
                                     "bold": True
                                   }
                                 },
                                 {
                                   "type": "emoji",
                                   "name": info["status"]
                                 }
                               ]
                             }
            else:
                list_block =  {
                               "type": "rich_text_section",
                               "elements": [
                                 {
                                   "type": "text",
                                   "text": job,
                                   "style": {
                                   "bold": True
                                   }
                                 },
                                 {
                                   "type": "text",
                                   "text": " This job has been disabled in CI variables config ",
                                   "style": {
                                   "bold": False
                                   }
                                 },
                                 {
                                  "type": "emoji",
                                  "name": "grimacing"
                                 }
                               ]
                             }
            all_affected_jobs_block.append(list_block)
        block = {
                 "type": "rich_text",
                 "elements": [
                   {
                     "type": "rich_text_section",
                     "elements": [
                       {
                         "type": "text",
                         "text": "Jobs which has been affected in this merge request:\n"
                       }
                     ]
                   },
                   {
                     "type": "rich_text_list",
                     "style": "bullet",
                     "elements": all_affected_jobs_block
                   }
                 ]
               }
        return block

    def _create_report(self, report_messages_message_dict, jobs_info):
        blocks = []
        for block_name, content_in_block in report_messages_message_dict.items():
            if block_name == "gitlabError":
                text = "There is error in gitlab response. Maybe merge request was merged?"
                blocks.append(self._create_plain_text_message_block(block_name, text))
            elif block_name == "affectedJobs":
              if len(content_in_block) == 0:
                text = "No jobs were affected."
                blocks.append(self._create_plain_text_message_block(block_name, text))
              else:
                  blocks.append(self._create_list_message_block(jobs_info))
        return blocks

    def post_results_to_thread_in_slack(self, channel_id, report_messages_message_dict, message_timestamp, msg_sender, jobs_info=None):
        if jobs_info != None:
            message_str = self._create_report(report_messages_message_dict, jobs_info)
        else:
            message_str = self._create_report(report_messages_message_dict, jobs_info)
        message = json.dumps(message_str)
        logging.debug(message)
        text = f"Hey <@{msg_sender}> your request has been processed!"
        self.client.chat_postMessage(channel=channel_id, thread_ts=message_timestamp, blocks=message, text=text)
