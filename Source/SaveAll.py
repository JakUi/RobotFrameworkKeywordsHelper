import json


def save_all(file_name, content):
    with open(f"Results/{file_name}", "w") as file:
        file.write(json.dumps(content, indent=2))
