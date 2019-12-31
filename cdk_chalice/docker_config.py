from typing import List
from dataclasses import dataclass


@dataclass
class DockerConfig:
    """ Class for keeping all docker build configuration in one place,
        use it in case your functions depend on packages that have
        natively compiled dependencies, use this class to build the Chalice app
        inside an AWS Lambda-like Docker container"""

    # :param docker_image: provide your docker image name, in case of empty will use default docker image
    docker_image: str = ""

    # :param docker_init_commands: provide list of commands to execute before 'chalice package'
    #             for example: ['pip install awscli --upgrade', 'pip install chalice']
    docker_init_commands: List[str] = None

    # :param environment_variables: environment variables to pass for docker container that build Chalice
    environment_variables = {}
