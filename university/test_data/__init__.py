import json


def _load_json(filename: str) -> dict:
    with open(filename, 'r') as f:
        return json.load(f)


degree_data = _load_json("university/test_data/degree_data.json")
course_data = _load_json("university/test_data/course_data.json")
