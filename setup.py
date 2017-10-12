from setuptools import setup, find_packages

setup(
    name='mmcontainers',
    version='0.1',
    author='Lars Kellogg-Stedman',
    author_email='lars@redhat.com',
    description=('An rsyslog plugin for annotating log messages '
                 'with kubernetse metadata'),
    license='GPLv3',
    url='https://github.com/larsks/mmcontainers',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'mmcontainers-cachedump=mmcontainers.cachedump:app.run',
            'mmcontainers-monitor=mmcontainers.monitor:app.run',
            'mmcontainers-filter=mmcontainers.filter:app.run',
        ],
    }
)
