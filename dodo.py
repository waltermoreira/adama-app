import os
import subprocess


def target_image_exists(img):
    """Check if 'img' exists in local registry"""

    def f():
        try:
            subprocess.check_output(
                'docker inspect {} 1>/dev/null 2>&1'.format(img),
                shell=True)
            return True
        except subprocess.CalledProcessError:
            return False
    return f


def task_build():

    all_files = ['deploy.yml', 'Dockerfile', 'dodo.py']
    for a_dir in ('stubs', 'handler', 'adama'):
        for d, _, fs in os.walk(a_dir):
            for f in fs:
                if f.endswith('.pyc'):
                    continue
                all_files.append(os.path.join(d, f))

    return {
        'actions': ['docker build -t adama/app .',
                    'docker inspect -f "{{ .Id }}" adama/app > .build'],
        'file_dep': all_files,
        'targets': ['.build'],
        'uptodate': [target_image_exists('adama/app')],
        'verbosity': 2
    }

