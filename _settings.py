import yaml

file_path = 'qa_robot_configer.yaml'


def read_configer(file):
    with open(file, mode='r', encoding='utf-8') as f:
        res = yaml.safe_load(f)
        return res


def write_configer(data):
    with open(file_path, mode="w", encoding='utf-8') as f:
        yaml.dump(data, f, encoding='utf-8', allow_unicode=True)


conf = read_configer(file_path)