from django.db import models
from django_hstore import forms, util


class HStoreDictionary(dict):
    """
    A dictionary subclass which implements hstore support.
    """
    def __init__(self, value=None, field=None, instance=None, **params):
        super(HStoreDictionary, self).__init__(value, **params)
        self.field = field
        self.instance = instance

    def remove(self, keys):
        """
        Removes the specified keys from this dictionary.
        """
        queryset = self.instance._base_manager.get_query_set()
        queryset.filter(pk=self.instance.pk).hremove(self.field.name, keys)


class HStoreDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is not None:
            return instance.__dict__[self.field.name]
        raise AttributeError

    def __set__(self, instance, value):
        if not isinstance(value, HStoreDictionary):
            value = self.field._attribute_class(value, self.field, instance)
        instance.__dict__[self.field.name] = value


class HStoreField(models.Field):

    _attribute_class = HStoreDictionary
    _descriptor_class = HStoreDescriptor

    def contribute_to_class(self, cls, name):
        super(HStoreField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, self._descriptor_class(self))

    def db_type(self, connection=None):
        return 'hstore'


class DictionaryField(HStoreField):
    """
    Stores a python dictionary in a postgresql hstore field.
    """
    def formfield(self, **params):
        params['form_class'] = forms.DictionaryField
        return super(DictionaryField, self).formfield(**params)

    def get_prep_lookup(self, lookup, value):
        return value

    def to_python(self, value):
        return value or {}

    def _value_to_python(self, value):
        return value


class ReferencesField(HStoreField):
    """
    Stores a python dictionary of references to model instances in an hstore field.
    """
    def formfield(self, **params):
        params['form_class'] = forms.ReferencesField
        return super(ReferencesField, self).formfield(**params)

    def get_prep_lookup(self, lookup, value):
        if isinstance(value, dict):
            return util.serialize_references(value)
        return value

    def get_prep_value(self, value):
        if value:
            return util.serialize_references(value)
        return {}

    def to_python(self, value):
        if value:
            return util.unserialize_references(value)
        return {}

    def _value_to_python(self, value):
        if value:
            return util.acquire_reference(value)
        return None


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules(rules=[], patterns=['django_hstore\.fields'])
except ImportError:
    pass
