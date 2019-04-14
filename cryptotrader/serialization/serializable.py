

class JsonSerializable(object):

    def serialize_json(self):
        raise NotImplementedError

    def deserialize_json(self):
        raise NotImplementedError
