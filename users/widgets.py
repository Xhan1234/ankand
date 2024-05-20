from django.contrib.admin.widgets import AdminTextInputWidget

class StateWidget(AdminTextInputWidget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'type': 'text', 'class': 'state-widget'})
        if value is not None and value != '':
            final_attrs['value'] = value
        return super().render(name, value, final_attrs, renderer)

class CityWidget(AdminTextInputWidget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'type': 'text', 'class': 'city-widget'})
        if value is not None and value != '':
            final_attrs['value'] = value
        return super().render(name, value, final_attrs, renderer)
