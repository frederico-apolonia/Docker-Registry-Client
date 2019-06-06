#! /usr/bin/env python3
"""
usage:
    docker-registry list [-s|--size]
    docker-registry list [-s|--size] <repository>
    docker-registry delete <repository> <tag>...
    docker-registry delete-range <repository> <from-tag> <to-tag>
    docker-registry delete-repository <repository>

note: environment variable DOCKER_REGISTRY_URL must be set for all functions to work
note: environment variable DOCKER_REGISTRY_DATA_PATH must be set for delete-repository to work
note: environment variable DOCKER_REGISTRY_DATA_PATH is expected to specify the path to 'var/lib/registry/docker/registry/v2'

"""

__version__ = "1.0.1"


from collections import defaultdict
import sys
import requests
import json
import re
import os
import shutil

from docopt import docopt


if 'DOCKER_REGISTRY_URL' not in os.environ:
    print(
        "Please set the environment variable DOCKER_REGISTRY_URL",
        file=sys.stderr,
    )
    sys.exit(2)

DOCKER_REGISTRY_URL = os.environ['DOCKER_REGISTRY_URL']


def get_repositories():
    request = requests.get('%s/v2/_catalog' % DOCKER_REGISTRY_URL)
    response = request.json()
    if 'repositories' not in response:
        print(
            "Error: unexpected response from server %s" % json.dumps(response),
            file=sys.stderr,
        )
        sys.exit(2)
    return response['repositories'] or []


def list_repositories(sort_by_size=False):
    repositories = get_repositories()
    if sort_by_size:
        repositories = [
            (get_repository_size(repository), repository)
            for repository in repositories
        ]
        repositories.sort(reverse=True)
        for size, repository in repositories:
            print(repository, readable_size(size))
    else:
        print(*repositories, sep='\n')


def get_layers(repository, digest):
    """returns a dict of digests and respective sizes for all layers associated with given digest"""
    url = '%s/v2/%s/manifests/%s' % (DOCKER_REGISTRY_URL, repository, digest)
    request = requests.get(url)
    return {
        layer['digest']: layer['size']
        for layer in request.json()['layers']
    }


def get_repository_size(repository):
    size_by_layer_digest = dict()
    for digest in get_repository_tags_digests(repository):
        size_by_layer_digest.update(get_layers(repository, digest))
    return sum(size_by_layer_digest.values())


def get_tags_sizes(repository):
    size_by_tag = dict()
    for digest, tag_group in get_repository_tags_digests(repository).items():
        size_by_layer_digest = dict(get_layers(repository, digest))
        size = sum(size_by_layer_digest.values())
        for tag in tag_group:
            size_by_tag[tag] = size
    return size_by_tag


def get_repository_tags_digests(repository):
    request = requests.get('%s/v2/%s/tags/list' % (DOCKER_REGISTRY_URL, repository))
    response = request.json()
    if 'tags' not in response:
        print(
            "Error: unexpected response from server %s" % json.dumps(response),
            file=sys.stderr,
        )
        sys.exit(2)
    tags = response["tags"] or []
    tags_by_digest = defaultdict(list)
    for tag in tags:
        digest = get_digest(repository, tag)
        tags_by_digest[digest].append(tag)
    return tags_by_digest


def get_tags(repository):
    tags_by_digest = get_repository_tags_digests(repository)
    tag_groups = list(tags_by_digest.values())
    for group in tag_groups:
        group.sort()
    tag_groups.sort(key=lambda group: group[0])
    return tag_groups


def get_digest(repository, tag):
    headers = {'Accept':'application/vnd.docker.distribution.manifest.v2+json'}
    tag_head_request = requests.head('%s/v2/%s/manifests/%s' % \
        (DOCKER_REGISTRY_URL, repository, tag), headers=headers).headers
    return tag_head_request['Docker-Content-Digest']


def list_tags(repository, sort_by_size=False):
    tags = get_tags(repository)
    if sort_by_size:
        tags_sizes = get_tags_sizes(repository)
        for group in tags:
            print(*group, readable_size(tags_sizes[group[0]]))
    else:
        for group in tags:
            print(*group)    


def delete_tag(repository, tag):
    headers = {'Accept':'application/vnd.docker.distribution.manifest.v2+json'}
    tag_digest = get_digest(repository, tag)
    request = requests.delete('%s/v2/%s/manifests/%s' % \
        (DOCKER_REGISTRY_URL, repository, tag_digest), headers=headers)
    if request.status_code != 202:
        print(
            "Error: unexpected response from server %s" % request,
            file=sys.stderr,
        )
        sys.exit(2)


def delete_repository(repository):
    # apaga a configuração
    # 1. listar os repositórios para garantir que vou apagar algo que existe
    # 2. se existe, então apagar
    if 'DOCKER_REGISTRY_DATA_PATH' not in os.environ:
        print(
            "Please set the environment variable DOCKER_REGISTRY_DATA_PATH before using delete_repository",
            file=sys.stderr,
        )
        sys.exit(2)

    docker_registry_data_path = os.environ['DOCKER_REGISTRY_DATA_PATH']
    src_folder =  '%s/repositories/%s/' % (docker_registry_data_path, repository)
    dest_folder = '%s/_deleted/%s' % (docker_registry_data_path, repository)
    
    # verificar se o repo ainda tem alguma tag
    if len(get_tags(repository)) != 0:
        print(
            "You can only delete repositories with no tags associated",
            file=sys.stderr,
        )
        sys.exit(2)
    
    os.chdir(docker_registry_data_path)

    if repository in os.listdir('./repositories/'):
        shutil.move(src_folder, dest_folder)
        os.chdir('./_deleted/')
        shutil.rmtree('./%s' % repository)
    else:
        print(
            "Please make sure you're pointing to /v2 folder or the repository exists",
            file=sys.stderr,
        )
    


def readable_size(size):
    orders = ['K', 'KB', 'MB', 'GB', 'TB']
    order_index = 0
    while size > 1024 and order_index < len(orders):
        size /= 1024.0
        order_index += 1

    return "{:.1f} %s".format(size) % orders[order_index]


def main():
    opts = docopt(__doc__)

    if opts["list"]:
        if opts["<repository>"] is not None:
            if opts["-s"] or opts["--size"]:
                list_tags(opts["<repository>"], sort_by_size=True)
            else:
                list_tags(opts["<repository>"])
        else:
            if opts["-s"] or opts["--size"]:
                list_repositories(sort_by_size=True)
            else:
                list_repositories()
    elif opts["delete"]:
        repository = opts["<repository>"]
        for tag in opts["<tag>"]:
            delete_tag(repository, tag)
    elif opts["delete-range"]:
        repository = opts["<repository>"]
        # replace asserts with print error and exit
        tag_groups = get_tags(repository)
        from_tag = opts["<from-tag>"]
        to_tag = opts["<to-tag>"]
        for i, group in enumerate(tag_groups):
            if from_tag in group:
                break
        else:
            print("Invalid tag: %s" % from_tag, file=sys.stderr)
            sys.exit(2)
        for k, group in enumerate(tag_groups):
            if to_tag in group:
                break
        else:
            print("Invalid tag: %s" % to_tag, file=sys.stderr)
            sys.exit(2)
        assert i < k
        for group in tag_groups[i:k+1]:
            try:
                delete_tag(repository, group[0])
                print("Deleted %s %s" % (repository, " ".join(group)))
            except:
                print("Error deleting %s" % tag, file=sys.stderr)
    elif opts["delete-repository"]:
        repository = opts["<repository>"]
        try:
            delete_repository(repository)
            print("Deleted %s" % repository)
        except:
            print("Error deleting %s" % repository)
    else:
        pass
        # error: Unknown command


if __name__ == "__main__":
    main()
