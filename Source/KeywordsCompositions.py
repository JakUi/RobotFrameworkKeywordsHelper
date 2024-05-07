import json
import logging


class KeywordsCompositions():

    def __init__(self, affected_keyword) -> None:
        self.includes_in_keywords = []
        self.affected_keyword = affected_keyword
        logging.basicConfig(level=logging.DEBUG)
        with open("Results/KeywordsDependencies.json") as dpds_file:
            self.all_deps = json.load(dpds_file)
        with open("Results/TestsCompositions.json") as tc_file:
            self.tests_compositions = json.load(tc_file)
        with open("Results/TestsSetups.json") as ts_file:
            self.tests_setups = json.load(ts_file)
 
    def keyword_contains_keywords(self):
        return self.all_deps.get(self.affected_keyword, "There is error in your request!")

    def contains_changeable_keyword(self):
        for key, value in self.all_deps.items():
            if self.affected_keyword in value:
                self.includes_in_keywords.append(key)
        return self.includes_in_keywords

    def tests_affects(self):
        affected_setup = self._check_affecting(self.tests_setups)
        if len(affected_setup) == 0:
            affected_tests = self._check_affecting(self.tests_compositions)
        else:
            affected_tests = [f"Setup has been affected in suite {affected_setup}"]
        text_affected_tests = 'Keyword *%s* affeсts tests:\n ```%s```' % (self.affected_keyword, affected_tests)
        logging.debug(text_affected_tests)
        return affected_tests, affected_setup

    def _check_affecting(self,to_check):
        affected = []
        for key, value in to_check.items():
            if self.affected_keyword in value:
                affected.append(key)
            for k in self.includes_in_keywords:
                if k in value:
                    affected.append(key)
        return affected

    def first_level_affects(self):
        pass

    def find_keyword_childs(self):
        text_keyword_consists_of = 'Keyword %s consists of keywords:\n %s' % (self.affected_keyword,
                       self.keyword_contains_keywords())
        text_keyword_included_in = 'Keyword %s included in keywords:\n %s' % (self.affected_keyword,
                                                                           self.contains_changeable_keyword())
        logging.debug(text_keyword_consists_of)
        logging.debug(text_keyword_included_in)
        return text_keyword_consists_of, text_keyword_included_in
