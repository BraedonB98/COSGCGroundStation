from builtins import super

class DataPoint:
    #copied from Darksky API to allow testing with edited forecasts
    def __init__(self, data):
        self._data = data

        if isinstance(self._data, dict):
            for name, val in self._data.items():
                setattr(self, name, val)

        if isinstance(self._data, list):
            setattr(self, 'data', self._data)

    def __setattr__(self, name, val):
        def setval(new_val=None):
            return object.__setattr__(self, name, new_val if new_val else val)

        if not isinstance(val, (list, dict)) or name == "_data":
            return setval()

        if name in ('alerts', 'flags'):
            return setval(eval(name.capitalize())(val))

        if isinstance(val, list):
            val = [DataPoint(v) if isinstance(v, dict) else v for v in val]
            return setval(val)

        setval(DataBlock(val) if 'data' in val.keys() else DataPoint(val))

    def __getitem__(self, key):
        return self._data[key]

    def __len__(self):
        return len(self._data)

class DataBlock(DataPoint):
    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, index):
        if isinstance(index, str):
            return self._data[index]
        return self.data.__getitem__(index)

    def __len__(self):
        return self.data.__len__()

class Flags(DataPoint):
    def __setattr__(self, name, value):
        return object.__setattr__(self, name.replace('-', '_'), value)

class Alerts(DataBlock):
    pass

class forecast_generator(DataPoint):
    def __init__(self, data):
        self._parameters = dict(latitude=40.0076, longitude=-105.2619, time=1)
        return super().__init__(data)

    def __setattr__(self, key, value):
        if key in ('_queries', '_parameters', '_data'):
            return object.__setattr__(self, key, value)
        return super().__setattr__(key, value)

    def __getattr__(self, key):
        currently = object.__getattribute__(self, 'currently')
        _data = object.__getattribute__(currently, '_data')
        if key in _data.keys():
            return _data[key]
        return object.__getattribute__(self, key)

    def __enter__(self):
        return self

    def __exit__(self, type, val, tb):
        del self