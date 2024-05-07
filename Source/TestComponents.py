import re
from SaveAll import save_all

class TestsCompositions():

    def __init__(self, tests_paths, tests_compositions, all_keywords):
        self.tests_files, self.tests_names = tests_paths, tests_compositions
        self.tests_compositions, self.setup_contains = dict(), dict()
        self.all_keywords = all_keywords

    def _get_all_tests_names_from_file(self, file):
        tests_declaration_block = False
        test_name, tests_tags = None, None
        tags_and_names = {"Tags": [], "Tests": []}
        self.setup_contains[file] = []
        with open(file, "r") as f:
            self.tests_names[file] = tags_and_names
            for line in f:
                line = line.replace("\n", "")
                tests_tags = self._get_tests_tags(line, tests_tags)
                self.tests_names[file]["Tags"] = tests_tags
                if tests_declaration_block == False and not line.startswith(" ") and not line.startswith("#") \
                and line != "":
                    keyword = re.search("(?<=  )(\w+ )+\w+", line)
                    if keyword:
                        for value in self.all_keywords.values():
                            if keyword.group() in value:
                                self.setup_contains[file].append(keyword.group())
                if line.count("Test Cases"):
                    tests_declaration_block = True
                elif tests_declaration_block == True and not line.startswith(" ") and not line.startswith("#") \
                and line != "":
                    self.tests_names[file]["Tests"].append(line)
                    self.tests_compositions[line] = []
                    test_name = line
                elif tests_declaration_block == True and line.startswith(" ") and not line.startswith("#") \
                and line != "" and not line.startswith("    [") and not line.startswith("    ..."):
                    substring = re.search("\s{4}(Given|When|Then|And)\s{1}(.*?)(\s{2}|$)", line)
                    if substring != None:
                        substring = substring.group(2)
                    if substring != "None":
                        self.tests_compositions[test_name].append(substring)

    def _get_tests_tags(self, line, tests_tags):
        if line.count("Tags"):
            tags_find_regex = "Tags\s*[a-zA-Z0-9\-\s]*?$|\[Tags\]\s*[a-zA-Z0-9\-\s]*?$|Force Tags\s*[a-zA-Z0-9\-_\s]*?$"
            row_tests_tags = re.search(tags_find_regex, line)
            if row_tests_tags != None:
                tests_tags = row_tests_tags.group(0)
                tests_tags = re.sub("Default Tags\s*|\[Tags\]\s*", "", line)
                tests_tags = re.sub("\\n", "", tests_tags).split()
        return tests_tags

    def get_tests_names_and_tags(self):
        for file in self.tests_files:
            self._get_all_tests_names_from_file(file)

    def save_tests_results(self):
        save_all(file_name="AllTests.json", content=self.tests_names)
        save_all(file_name="TestsSetups.json", content=self.setup_contains)
        save_all(file_name="TestsCompositions.json", content=self.tests_compositions)
