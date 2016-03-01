from setuptools import setup, find_packages

setup(
    name="burst",
    version='1.0.36',
    zip_safe=False,
    platforms='any',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires=['setproctitle', 'twisted', 'events', 'netkit'],
    scripts=['burst/bin/burstctl.py'],
    url="https://github.com/dantezhu/burst",
    license="MIT",
    author="dantezhu",
    author_email="zny2008@gmail.com",
    description="twisted with master, proxy and worker",
)
