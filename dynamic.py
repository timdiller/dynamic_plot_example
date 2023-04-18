import numpy as np

from chaco.api import ArrayPlotData, Plot
from enable.api import ComponentEditor
from pyface.api import CANCEL, FileDialog, OK
from traits.api import Array, DelegatesTo, Event, HasStrictTraits, Instance, List, Property, Str
from traitsui.api import (
    ButtonEditor, CheckListEditor, Group, HGroup, HSplit, ListEditor, InstanceEditor, Item, 
    Spring, VGroup, View,
)


class DrillData(HasStrictTraits):
    data = Array()
    channels = Property(depends_on='data')

    def _get_channels(self):
        return self.data.dtype.names if self.data is not None else []

class ChannelView(HasStrictTraits):
    data = Instance(DrillData)
    name = Str()
    plot = Instance(Plot)
    traits_view = View(
        VGroup(
            Item('plot', editor=ComponentEditor(),),
            Item('name'),
        ),
    ),

class DataView(HasStrictTraits):
    drill_data = Instance(DrillData)
    filename = Str()
    open_file = Event()
    channels = Property(depends_on="drill_data")
    selected_channels = List()
    channel_views = Property(List(Instance(ChannelView)), depends_on='selected_channels')

    def _get_channels(self):
        if self.drill_data is not None:
            channels = list(self.drill_data.channels)
            channels.remove("DEPTH")
            return channels
        else:
            return []
    
    def _get_channel_views(self):
        return [ChannelView(name=channel) for channel in self.selected_channels]

    def _open_file_fired(self):
        fd = FileDialog()
        status = fd.open()
        if status == OK:
            self.filename = fd.filename
            data = np.genfromtxt(fd.path, names=True)
            self.drill_data = DrillData(data=data)
    
data_view = View(
    HSplit(
        Group(
            HGroup(
                Item('filename', style='readonly'),
                Item('open_file', editor=ButtonEditor(label="Open File..."), show_label=False, )
            ),
            Group(
                Item(
                    'selected_channels',
                    editor=CheckListEditor(name='channels', cols=2),
                    show_label=False,
                    style='custom',
                ),
            ),
            show_border=True,
        ),
        Group(
            Item(
                'channel_views', 
                editor=ListEditor(
                    editor=InstanceEditor(),
                    style='custom',
                ),
                style='readonly',
                show_label=False,
            ),
            springy=True,
        ),
    ),
    resizable=True,
    height=500,
    width=500,
)


if __name__ == "__main__":
    dv = DataView()
    dv.configure_traits(view=data_view)