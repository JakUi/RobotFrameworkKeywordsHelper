import re
import logging
import os
from Executor import Executor
from SlashCommands import SlashCommands
from multiprocessing import Process, Queue
from flask import Flask, request, abort, render_template


app = Flask(__name__)

def get_request_data():
    form_data = request.form
    data = form_data.copy().to_dict(flat=False)
    return data

class Server:

    def __init__(self, queue) -> None:
        self.queue = queue

    def event_handler(sef):
        @app.route('/webhook', methods=['POST'])
        def get_webhook():
            if request.method == 'POST':
                queue.put(request.json)
                return 'success', 200
            else:
                abort(400)

        @app.route('/report', methods=['GET'])
        def report():
            return render_template('index.html')

        @app.route('/command', methods=['POST'])
        def get_bot_command():
            queue.put(get_request_data())
            return 'Your command has been accepted and now is being executed.', 200

        @app.errorhandler(404)
        def page_not_found(e):
            form_data = request.form
            logging.debug(form_data)
            return 'Error', 404

        app.run(host='0.0.0.0')

class HelperBot:
    
    def __init__(self) -> None:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("slack_sdk.web.base_client").disabled = True
        self.executor = Executor()
        self.commands_list = ["/help", "/keyword-composition", "/tests-affects", "/jobs-affects", "/keyword-info"]

    def _get_merge_request_url(self, received_msg):
        merge_requests_urls_list = []
        # Извлекает из текста содержащего ссылку вида https://gitlab.octafx.com/qa/customer-facing-tests/-/merge_requests/1467
        # строку вида /merge_requests/XXXX где XXXX - номер мерж реквеста
        message_text = received_msg["event"]["text"]
        self.msg_timestamp = received_msg["event"]["ts"]
        self.msg_sender = received_msg["event"]["user"]
        reg = re.findall("merge_requests\/\d+", message_text)
        merge_requests_urls_list = ["https://gitlab.octafx.com/api/v4/projects/383/merge_requests/" \
                                    + mr[mr.find("/") + 1 : ] for mr in reg]
        logging.debug("Message contains merge requests: %s" % (merge_requests_urls_list))
        return merge_requests_urls_list

    def _run_command(self, received_msg):
        response_url = received_msg.get("response_url")[0]
        SC = SlashCommands(response_url=response_url)
        slash_command = received_msg.get("command")
        command_text = received_msg.get("text", None)[0]
        find_command_text = re.search("[a-zA-Z]", command_text)
        if find_command_text == None:
            has_command_text = False
        else:
            has_command_text = True
            keyword_consists_of, keyword_included_in, affected_tests, affected_suites, affected_jobs = \
            self.executor.command_flow(command_text)
        if slash_command[0] == "/help":
            SC.response_on_slash_command("/help", None)
        elif slash_command[0] == "/keyword-composition" and has_command_text != False:
            SC.response_on_slash_command("/keyword-composition", command_text, " consists of keywords:\n",
                                          keyword_consists_of)
            SC.response_on_slash_command("/keyword-composition", command_text, " included in keywords:\n",
                                          keyword_included_in)
        elif slash_command[0] == "/tests-affects" and has_command_text != False:
            SC.response_on_slash_command("/tests-affects", command_text, " affects tests:\n", affected_tests)
            SC.response_on_slash_command("/tests-affects", command_text, " affects suites:\n", affected_suites)
        elif slash_command[0] == "/jobs-affects" and has_command_text != False:
            SC.response_on_slash_command("/jobs-affects", command_text, " affects jobs:\n", affected_jobs)
        elif slash_command[0] == "/keyword-info" and has_command_text != False:
            SC.response_on_slash_command("/keyword-composition", command_text, " consists of keywords:\n",
                                          keyword_consists_of)
            SC.response_on_slash_command("/keyword-composition", command_text, " included in keywords:\n",
                                          keyword_included_in)
            SC.response_on_slash_command("/tests-affects", command_text, " affects tests:\n", affected_tests)
            SC.response_on_slash_command("/tests-affects", command_text, " affects suites:\n", affected_suites)
            SC.response_on_slash_command("/jobs-affects", command_text, " affects jobs:\n", affected_jobs)
        elif slash_command[0] in self.commands_list and has_command_text == False:
            SC.response_on_slash_command(slash_command[0], None, has_command_text=has_command_text)

    def _message_processing(self, received_msg):
        channel, merge_requests_urls_list = None, None
        if "event" in received_msg and "text" in received_msg["event"]:
            message_text = received_msg["event"]["text"]
            self.msg_timestamp = received_msg["event"]["ts"]
            self.msg_sender = received_msg["event"]["user"]
            reg = re.findall("customer-facing-tests\/-\/merge_requests\/\d+", message_text)
            merge_requests_urls_list = ["https://gitlab.octafx.com/api/v4/projects/383/merge_requests/" \
                                        + mr[mr.rfind("/") + 1 : ] for mr in reg]
            logging.debug("Message contains merge requests: %s" % (merge_requests_urls_list))
            channel = received_msg["event"]["channel"]
        elif "command" in received_msg:
            self._run_command(received_msg)
        else:
            logging.debug("Something wrong with the event message: %s" %(received_msg))
        return merge_requests_urls_list, channel

    def run_executor(self):
        os.system('git config --global http.sslVerify false') # Если сработает, читай тут:
        # https://menetray.com/en/blog/git-error-problem-ssl-certificate-verify-certif-ca-ok нужно сделать красиво
        
        os.system('git config --global user.email "you@example.com" && git config --global user.name "KWHelper"')
        while True:
            received_msg = server.queue.get()
            logging.debug("Message:\n %s" % str(received_msg))
            if received_msg:
                merge_requests_urls_list, channel = self._message_processing(received_msg)
                if merge_requests_urls_list:
                    self.executor.merge_request_flow(merge_requests_urls_list, message_timestamp=self.msg_timestamp,
                                                msg_sender=self.msg_sender, channel_id=channel)

if __name__ == '__main__':
    queue = Queue()
    server = Server(queue)
    bot = HelperBot()
    p1 = Process(target=server.event_handler)
    p2 = Process(target=bot.run_executor)
    p1.start()
    p2.start()
    p1.join()
    p2.join()
