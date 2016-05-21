from setuptools import setup, find_packages

setup(
    name="burst",
    version='1.0.81',
    zip_safe=False,
    platforms='any',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    scripts=['burst/bin/burstctl'],
    install_requires=['setproctitle', 'twisted', 'events', 'netkit', 'click'],
    url="https://github.com/dantezhu/burst",
    license="MIT",
    author="dantezhu",
    author_email="zny2008@gmail.com",
    description="twisted with master, proxy and worker",
)
