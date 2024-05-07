import os


class GetFiles:

    def __init__(self):
        self.resource_files, self.tests_files = [], []
        self.keywords_names, self.tests_names = dict(), dict()

    def _get_names_from_file(self, path_to_folder, files, names):
        folders = []
        for object in os.listdir(path_to_folder):
            object = os.path.join(path_to_folder, object)
            if os.path.isfile(object) and object.endswith('.robot'):
                files.append(object)
                names[object] = []
            elif os.path.isdir(object):
                folders.append(object)
        for folder in folders:
            self._get_names_from_file(folder, files, names)
        return files, names

    def get_all_from_files(self):
        resource_files, tests_files = [], []
        keywords_names, tests_names = dict(), dict()
        resource_files, keywords_names = self._get_names_from_file(
                                              "TMP/customer-facing-tests/Resources", resource_files, keywords_names
                                              )
        tests_files, tests_names = self._get_names_from_file(
                                        "TMP/customer-facing-tests/Tests", tests_files, tests_names
                                        )
        self.resource_files, self.keywords_names = resource_files, keywords_names
        self.tests_files, self.tests_names = tests_files, tests_names
