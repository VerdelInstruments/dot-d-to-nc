import tempfile
import zipfile
import os

def zip_dot_d_file(dot_d_path: str):
    """
    Creates a temporary zip file from a .d directory.
    :param dot_d_path: Path to the .d directory to be zipped.
    :return: Path to the created zip file.
    """
    if not os.path.isdir(dot_d_path) or not dot_d_path.endswith('.d'):
        raise ValueError(f"{dot_d_path} is not a valid .d directory.")

    base_name = os.path.basename(dot_d_path.rstrip('/'))

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, f"{base_name}.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dot_d_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dot_d_path)
                    zipf.write(file_path, arcname)

    print('zipped file:', zip_path)
    return zip_path



if __name__ == '__main__':
    file = '/Users/joseph/Documents/verdel/240927_TrailCID_SWIM_01.d'

    zip_dot_d_file(file)