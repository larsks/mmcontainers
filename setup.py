from setuptools import setup, find_packages

setup(
    name='mmkubernetes',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@redhat.com',
    description=('An rsyslog plugin for annotating log messages '
                 'with kubernetse metadata'),
    license='GPLv3',
    url='https://github.com/larsks/mmkubernetes',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mmkubernetes=mmkubernetes.main:main',
        ],
    }
)
