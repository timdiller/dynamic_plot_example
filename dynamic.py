import numpy as np

from chaco.api import ArrayPlotData, HPlotContainer, Plot
from chaco.tools.api import PanTool, BetterSelectingZoom
from enable.api import ComponentEditor
from pyface.api import CANCEL, FileDialog, OK
from traits.api import (
    Array, DelegatesTo, Event, HasTraits, HasStrictTraits, Instance, List, Property, Str,
    cached_property,
)
from traitsui.api import (
    ButtonEditor, CheckListEditor, Group, HGroup, HSplit, ListEditor, InstanceEditor, Item, 
    Spring, VGroup, View,
)

DEPTH = "DEPTH"
MISSING_VALUE = -999.25


class DrillData(HasStrictTraits):
    data = Array()
    channels = Property(depends_on='data')

    def _get_channels(self):
        return self.data.dtype.names if self.data is not None else []

class ChannelsView(HasTraits):
    data = Instance(DrillData)
    channels = List()
    plots = Instance(HPlotContainer)

    def _plots_default(self):
        plots = []
        # import ipdb;  ipdb.set_trace()
        if self.data is not None:
            data_dict = {chan: self.data.data[chan] for chan in self.channels}
            data_dict[DEPTH] = self.data.data[DEPTH]
            apd = ArrayPlotData(**data_dict)
            
            for channel in self.channels:
                plot = Plot(apd)
                plot.plot((channel, DEPTH), origin='top left')
                plot.title = channel
                if len(plots) >= 1:
                    plot.value_axis.visible = False
                plot.tools.append(PanTool(plot, constrain=True, constrain_direction='x'))
                plot.overlays.append(BetterSelectingZoom(plot, axis='index', zoom_factor=1.05))
                plots.append(plot)
        hpc = HPlotContainer(*plots, spacing=1)
        return hpc

channel_plots_editor = InstanceEditor(
    view=View(Item('plots', editor=ComponentEditor(), show_label=False))
)


class DataView(HasStrictTraits):
    drill_data = Instance(DrillData)
    filename = Str()
    open_file = Event()
    channels = Property(depends_on="drill_data")
    selected_channels = List()
    channels_view = Property(Instance(ChannelsView), depends_on="selected_channels")

    def _get_channels(self):
        if self.drill_data is not None:
            channels = list(self.drill_data.channels)
            channels.remove(DEPTH)
            return channels
        else:
            return []
        
    @cached_property
    def _get_channels_view(self):
        return ChannelsView(data=self.drill_data, 
                            channels=self.selected_channels)


    def _open_file_fired(self):
        fd = FileDialog()
        status = fd.open()
        if status == OK:
            self.filename = fd.filename
            data = np.genfromtxt(fd.path, names=True)
            for name in data.dtype.names:
                data[name][data[name] == MISSING_VALUE] = np.nan
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
                'channels_view', 
                editor=channel_plots_editor,
                style='custom',
                show_label=False,
            ),
            springy=True,
        ),
    ),
    resizable=True,
    height=500,
    width=1000,
)


if __name__ == "__main__":
    dv = DataView()
    dv.configure_traits(view=data_view)