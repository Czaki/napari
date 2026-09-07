import pytest

from napari.utils.migrations import (
    DeprecatedProperty,
    _DeprecatingDict,
    add_deprecated_property,
    deprecated_class_name,
    rename_argument,
)


def test_simple():
    @rename_argument('a', 'b', '1', '0.5')
    def sample_fun(b):
        return b

    assert sample_fun(1) == 1
    assert sample_fun(b=1) == 1
    with pytest.deprecated_call():
        assert sample_fun(a=1) == 1
    with pytest.raises(ValueError, match='already defined'):
        sample_fun(b=1, a=1)


def test_constructor():
    class Sample:
        @rename_argument('a', 'b', '1', '0.5')
        def __init__(self, b) -> None:
            self.b = b

    assert Sample(1).b == 1
    assert Sample(b=1).b == 1
    with pytest.deprecated_call():
        assert Sample(a=1).b == 1


def test_deprecated_property() -> None:
    @add_deprecated_property('old_property', 'new_property', '0.1.0', '0.0.0')
    class Dummy:
        def __init__(self) -> None:
            self._value = 0

        @property
        def new_property(self) -> int:
            return self._value

        @new_property.setter
        def new_property(self, value: int) -> int:
            self._value = value

    instance = Dummy()

    assert instance.new_property == 0

    instance.new_property = 1

    msg = 'Dummy.old_property is deprecated since 0.0.0 and will be removed in 0.1.0. Please use new_property'

    with pytest.warns(FutureWarning, match=msg):
        assert instance.old_property == 1

    with pytest.warns(FutureWarning, match=msg):
        instance.old_property = 2

    assert instance.new_property == 2


def test_deprecated_class_name():
    """Test the deprecated class name function."""

    class macOS:
        pass

    MacOSX = deprecated_class_name(
        macOS, 'MacOSX', version='10.12', since_version='10.11'
    )

    with pytest.warns(FutureWarning, match='deprecated.*macOS'):
        _os = MacOSX()

    with pytest.warns(FutureWarning, match='deprecated.*macOS'):

        class MacOSXServer(MacOSX):
            pass


def test_deprecating_dict_with_renamed_in_deprecated_keys():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    assert 'c' in d.deprecated_keys


def test_deprecating_dict_with_renamed_getitem_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d['c'] == 1


def test_deprecating_dict_with_renamed_get_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d.get('c') == 1


def test_deprecating_dict_with_renamed_set_nondeprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )

    d['a'] = 3

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d['c'] == 3


def test_deprecating_dict_with_renamed_set_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )

    with pytest.warns(FutureWarning, match='is deprecated since'):
        d['c'] = 3

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d['c'] == 3
    assert d['a'] == 3


def test_deprecating_dict_with_renamed_update_nondeprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )

    d.update({'a': 3})

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d['c'] == 3


def test_deprecating_dict_with_renamed_update_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )

    with pytest.warns(FutureWarning, match='is deprecated since'):
        d.update({'c': 3})

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert d['c'] == 3
    assert d['a'] == 3


def test_deprecating_dict_with_renamed_del_nondeprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    assert 'a' in d
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' in d

    with pytest.warns(FutureWarning, match='is deprecated since'):
        del d['c']

    assert 'a' not in d
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' not in d


def test_deprecating_dict_with_renamed_del_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' in d
    assert 'a' in d

    with pytest.warns(FutureWarning, match='is deprecated since'):
        del d['c']

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' not in d
    assert 'a' not in d


def test_deprecating_dict_with_renamed_pop_nondeprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    assert 'a' in d
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' in d

    with pytest.warns(FutureWarning, match='is deprecated since'):
        d.pop('c')

    assert 'a' not in d
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' not in d


def test_deprecating_dict_with_renamed_pop_deprecated():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )
    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' in d
    assert 'a' in d

    with pytest.warns(FutureWarning, match='is deprecated since'):
        d.pop('c')

    with pytest.warns(FutureWarning, match='is deprecated since'):
        assert 'c' not in d
    assert 'a' not in d


def test_deprecating_dict_with_renamed_copy():
    d = _DeprecatingDict({'a': 1, 'b': 2})
    d.set_deprecated_from_rename(
        from_name='c', to_name='a', version='v2.0', since_version='v1.6'
    )

    e = d.copy()

    assert d is not e
    assert e.data == d.data
    assert e.deprecated_keys == d.deprecated_keys


def test_deprecated_property_descriptor():
    class Sample:
        def __init__(self):
            self._value = 0

        @property
        def new_property(self):
            return self._value

        @new_property.setter
        def new_property(self, value):
            self._value = value

        old_property = DeprecatedProperty(
            'new_property',
            '0.1.0',
        )

    instance = Sample()

    assert instance.new_property == 0

    instance.new_property = 1

    msg = 'Sample.old_property is deprecated since 0.1.0. Please use new_property'

    with pytest.warns(FutureWarning, match=msg):
        assert instance.old_property == 1

    with pytest.warns(FutureWarning, match=msg):
        instance.old_property = 2

    assert instance.new_property == 2


def test_deprecated_property_descriptor_nested():
    class SubSample:
        def __init__(self):
            self.value = 0

    class Sample:
        def __init__(self):
            self.subsample = SubSample()

        old_property = DeprecatedProperty(
            'subsample.value',
            '0.1.0',
        )

    instance = Sample()

    assert instance.subsample.value == 0

    with pytest.warns(
        FutureWarning, match='Sample.old_property is deprecated since 0.1.0'
    ):
        assert instance.old_property == 0

    with pytest.warns(
        FutureWarning, match='Sample.old_property is deprecated since 0.1.0'
    ):
        instance.old_property = 1

    assert instance.subsample.value == 1


def test_deprecated_property_descriptor_no_writing():
    class Sample:
        def __init__(self):
            self._value = 0

        @property
        def new_property(self):  # pragma: no cover
            return self._value

        old_property = DeprecatedProperty(
            'new_property', '0.1.0', writable=False
        )

    instance = Sample()

    with pytest.raises(AttributeError, match='has no setter'):
        instance.old_property = 1

    with pytest.raises(AttributeError, match='has no setter'):
        instance.new_property = 2
