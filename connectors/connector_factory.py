from abc import abstractmethod


class ObjectFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, key, builder):
        self._builders[key] = builder

    def create(self, key, **kwargs):
        builder = self._builders.get(key)
        if not builder:
            raise ValueError(f"Connector or Property factory has no builder for {key}")
        return builder.build(**kwargs)


class ObjectBuilder:
    def __init__(self):
        pass

    @abstractmethod
    def build(self, **kwargs):
        pass


connector_factory = ObjectFactory()
property_factory = ObjectFactory()
