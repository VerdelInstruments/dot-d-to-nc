import yaml

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)

    return config
