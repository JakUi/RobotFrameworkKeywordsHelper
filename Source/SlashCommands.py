import logging
import json
import requests


class SlashCommands():

    def __init__(self, response_url) -> None:
        self.response_url = response_url
        logging.basicConfig(level=logging.DEBUG)
        self.slash_commands = {
                               "/help": {"syntax": "/help", "describe": " - command returns info about all bot commands"},
                               "/keyword-composition": {"syntax": "/keyword-composition keyword name", "describe": " - command returns info about keyword compositon (which keywords this keyword contain)"},
                               "/tests-affects": {"syntax": "/tests-affects keyword name", "describe": " - command returns info about affected tests (which tests this keyword affects)"},
                               "/jobs-affects": {"syntax": "/jobs-affects keyword name", "describe": " - command returns info about affected jobs (which job this keyword affects)"},
                               "/keyword-info": {"syntax": "/keyword-info keyword name", "describe": " - command returns all info about keyword"}
                              }
     
    def _create_help_command_message_block(self, command_description):
        command_message_block = {
                                 "blocks": [
                                   {
                                     "type": "rich_text",
                                     "elements": [
                                       {
                                         "type": "rich_text_section",
                                         "elements": [
                                           {
                                             "type": "text",
                                             "text": command_description
                                           }
                                         ]
                                       }
                                     ]
                                   }
                                 ]
                                }
        return command_message_block

    def _create_all_commands_block(self, command, command_description):
        command_block = {
                          "type": "rich_text_list",
                          "style": "bullet",
                          "elements": [
                            {
                              "type": "rich_text_section",
                              "elements": [
                                {
                                  "type": "text",
                                  "text": command,
                                  "style": {
                                  "bold": True
                                }
                                },
                                {
                                  "type": "text",
                                  "text": command_description
                                }
                              ]
                            }
                          ]
                        }
        return command_block

    def _keyword_name_block(self, keyword_name, keyword_action): # Это блок с названием кейворда
        command_description_block = {
                                      "blocks": [
                                        {
                                          "type": "rich_text",
                                          "elements": [
                                            {
                                              "type": "rich_text_section",
                                              "elements": [
                                                {
                                                  "type": "text",
                                                  "text": "Keyword ",
                                                  "style": {
                                                    "bold": False
                                                  }
                                                },
                                                {
                                                  "type": "text",
                                                  "text": keyword_name,
                                                  "style": {
                                                    "bold": True
                                                  }
                                                },
                                                {
                                                  "type": "text",
                                                  "text": keyword_action,
                                                  "style": {
                                                    "bold": False
                                                  }
                                                }
                                              ]
                                            }
                                          ]
                                        }
                                      ]
                                    }
        return command_description_block
    
    def _create_keyword_element_block(self, element):
        keyword_elements_block = {
                                  "type": "rich_text_list",
                                  "style": "bullet",
                                  "elements": [
                                    {
                                      "type": "rich_text_section",
                                      "elements": [
                                        {
                                          "type": "text",
                                          "text": element
                                        }
                                      ]
                                    }
                                  ]
                                 }
        return keyword_elements_block

    def _create_help_command_response_block(self):
        command, command_description = "/help", "List of all bot commands:\n"
        command_message_block = self._create_help_command_message_block(command_description)
        for command, command_description in self.slash_commands.items():
            command_block = self._create_all_commands_block(command, command_description["describe"])
            command_message_block["blocks"][0]["elements"].append(command_block)
        return command_message_block

    def _create_keyword_composition_command_response_block(self, keyword_name, keyword_action, elements_list):
        command_message_block = self._keyword_name_block(keyword_name, keyword_action)
        for element in elements_list:
            command_block = self._create_keyword_element_block(element)
            command_message_block["blocks"][0]["elements"].append(command_block)
        return command_message_block
    
    def _return_command_info(self, command):
        syntax = self.slash_commands[command]["syntax"]
        msg = {
                "blocks": [
                  {
                    "type": "section",
                    "text": {
                      "type": "mrkdwn",
                      "text": "There is an error in your request, please rewrite it using command syntax:\n" +
                        f"*`{syntax}`*"
                    }
                  }
                ]
              }
        return msg
    
    def response_on_slash_command(self, command, command_text, keyword_action=None, elements_list=None, has_command_text=True):
        keyword_name = command_text
        if command == "/help":
            message = json.dumps(self._create_help_command_response_block())
        else:
            if has_command_text == False:
                message = json.dumps(self._return_command_info(command))
            else:
                message = json.dumps(self._create_keyword_composition_command_response_block(keyword_name, keyword_action,
                                                                                        elements_list))
        logging.debug(message)
        headers = {'Content-Type': 'application/json'}
        requests.request("POST", self.response_url, headers=headers, data=message)

            #     SC.response_on_slash_command("/help")  Done!!!
            # elif slash_command[0] == "/keyword-composition":  Done!!!
            #     SC.response_on_slash_command("/keyword-composition")
            # elif slash_command[0] == "/tests-affects":  Done!!!
            #     SC.response_on_slash_command("/tests-affects")
            # elif slash_command[0] == "/jobs-affects":  Done!!!
            #     SC.response_on_slash_command("/jobs-affects")
            # elif slash_command[0] == "/keyword-info":
            #     SC.response_on_slash_command("/keyword-info")