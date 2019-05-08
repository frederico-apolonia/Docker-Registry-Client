================
 docker-registry-functions
================

``search-replace`` is a trivial Python script that implements
search/replace in text files.

``docker-registry-functions`` is a Python script that implements Docker Registry functions such as: listing repositories, listing tags from a repository, delete tags and delete a repository.

GITHUB

Copyright (c) 2019 Frederico Apolónia <fredericojcapolo@gmail.com>

Usage
-----

    docker-registry list [-s|--size]
    docker-registry list [-s|--size] <repository>
    docker-registry delete <repository> <tag1> <tag2> ...
    docker-registry delete-range <repository> <from-tag> <to-tag>
    docker-registry delete-repository <repository>

**Note**: environment variable ``DOCKER_REGISTRY_URL`` must be set for all functions to work
**Note**: environment variable ``DOCKER_REGISTRY_DATA_PATH`` must be set for delete-repository to work
**Note**: environment variable ``DOCKER_REGISTRY_DATA_PATH`` is expected to specify the path to ``var/lib/registry/docker/registry/v2``

Where list will either:

* List all repositories present on a specified docker registry
* List all tags from a ``<repository>``
