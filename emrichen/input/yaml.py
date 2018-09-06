from collections import OrderedDict
from functools import partial

import yaml

from emrichen.tags.base import tag_registry


def _construct_tagless_yaml(loader, node):
    # From yaml.constructor.BaseConstructor#construct_object
    if isinstance(node, yaml.ScalarNode):
        constructor = loader.construct_scalar
    elif isinstance(node, yaml.SequenceNode):
        constructor = loader.construct_sequence
    elif isinstance(node, yaml.MappingNode):
        constructor = loader.construct_mapping
    return constructor(node)


def _load_yaml_tag(tag, loader, node):
    data = _construct_tagless_yaml(loader, node)
    return tag(data)


class RichLoader(yaml.SafeLoader):
    def __init__(self, stream):
        super(RichLoader, self).__init__(stream)
        self.add_tag_constructors()

    def add_tag_constructors(self):
        self.yaml_constructors = self.yaml_constructors.copy()  # Grab an instance copy from the class
        self.yaml_constructors[self.DEFAULT_MAPPING_TAG] = self._make_ordered_dict
        for name, tag in tag_registry.items():
            self.yaml_constructors[f'!{name}'] = partial(_load_yaml_tag, tag)

    @staticmethod
    def _make_ordered_dict(loader, node):
        loader.flatten_mapping(node)
        return OrderedDict(loader.construct_pairs(node))


def load_yaml(data):
    return list(yaml.load_all(data, Loader=RichLoader))