import copy
import re
from SaveAll import save_all

class KeywordsAndDependencies:

    def __init__(self, keywords, resource_files):
        self.keywords = keywords
        self.resource_files = resource_files
        self.keywords_list = []
        self.keywords_dependencies, self.keywords_paths = dict(), dict()

    def _get_all_parent_keywords_from_file(self, resource_file):
        keywords_declaration_block = False
        with open(resource_file, "r") as file:
            for line in file:
                line = line.replace("\n", "")
                if line.count("* Keywords *"):
                    keywords_declaration_block = True
                elif keywords_declaration_block is True and not line.startswith(" ") and not line.startswith("#") and line != "":
                    self.keywords_list.append(line)

    def _get_all_nested_keywords_from_file(self, resource_file):
        keywords_declaration_block, parent_keyword = False, None
        substrings_list = []
        with open(resource_file, "r") as file:
            for line in file:
                line = line.replace("\n", "")
                if line.count("* Keywords *"):
                    keywords_declaration_block = True
                elif keywords_declaration_block is True and not line.startswith(" ") and not line.startswith("#") and line != "":
                    parent_keyword = line
                    self.keywords[resource_file].append(line)
                    self.keywords_paths[line] = resource_file
                    if parent_keyword not in self.keywords_dependencies:
                        self.keywords_dependencies[parent_keyword] = []
                elif keywords_declaration_block and line.startswith(" ") or line.startswith("..."):
                    substrings_list = re.split("\s{2,}", line)
                    for substring in substrings_list:
                        if substring in self.keywords_list and substring != parent_keyword and substring \
                            not in self.keywords_dependencies[parent_keyword]:
                            self.keywords_dependencies[parent_keyword].append(substring)

    def get_all_keywords(self):
        for file in self.resource_files:
            self._get_all_parent_keywords_from_file(file)
        for rf in self.resource_files:
            self._get_all_nested_keywords_from_file(rf)

    def _get_child_dependencies(self, dependencies):
        all_parent_dpds = copy.deepcopy(dependencies)
        for k, v in dependencies.items():
            for e in v:
                if dependencies[e] != []:
                    for elem in dependencies[e]:
                        if elem not in all_parent_dpds[k]:
                            all_parent_dpds[k].append(elem)
        dependencies = None
        return all_parent_dpds

    def get_all_dependencies(self):
        dependencies = self.keywords_dependencies
        n_1 = dependencies
        n = None
        while n != n_1:
            n_1 = dependencies
            dependencies = self._get_child_dependencies(dependencies)
            n = dependencies
        return dependencies

    def save_keywords_results(self):
        save_all("AllKeywords.json", self.keywords)
        save_all("KeywordsDependencies.json", self.get_all_dependencies())
