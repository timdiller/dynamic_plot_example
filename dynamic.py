# Yui's comments.
# To understand code, I'll try to add comments on each function / process

# importing packages.
# chaco.api: https://docs.enthought.com/chaco/
# enable.api: Primal functions under Chaco (OS-> Qt -> Kiva -> Enable (HTML5 Canvas) -> Chaco (p5.js) ?) https://docs.enthought.com/enable/
# pyface.api: GUI abstraction layers for TraitsUI https://docs.enthought.com/pyface/
# traist.api: https://docs.enthought.com/traits/
# traitsui.api: https://docs.enthought.com/traitsui/

import numpy as np
from chaco.api import ArrayPlotData, HPlotContainer, Plot
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

# Read files and set data.
# channels are ["DEPTH", "VS"...] like Property to get keys of data.
# Question: when the data will be set?
class DrillData(HasStrictTraits):
    data = Array()
    channels = Property(depends_on='data')

    def _get_channels(self):
        return self.data.dtype.names if self.data is not None else []

# Create model and view for visualization.
# HPlotContainer is a chaco module that contains multiple plots.
# You can just plot = Plot(data), plots.append(plot) then HPlotContainer(*plots).
# _plots_default will be called on View(Item("plots")... as plots is called.

# Note that it creates ArrayPlotData like
# apd = ArrayPlotData({"DEPTH": [313.0, 232.0 ...], })
# then create each plot like
# plot = Plot(apd)

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
                plots.append(plot)
        hpc = HPlotContainer(*plots)
        return hpc

# About Editor:
# ("channels", editor=CheckListEditor) means "Please show the channels in the form of checklist"
# ("channels", editor=TableEditor) means "Please show the channels in the form of table"

# This is a custom Editor which wraps ComponentEditor.
# Note that the view is set as a arg.
# Note that InstanceEditor is a TraitsUI module
# while ComponentEditor is a Chaco module.
# A InstanceEditor has a ComponentEditor as a canvas.
# You cannot show a graph without ComponentEditor because it's a canvas.

channel_plots_editor = InstanceEditor(
    view=View(Item('plots', editor=ComponentEditor(), show_label=False))
)

# This view holds file and data information althought 
# the raw_data is held by DrillData instance (which provides util to get keys as well).
# Here open_file is an Event which will have _[name_of_variable]_fired function.
# The Event can be a button if you set it like Item("open_file", editor=ButtonEditor...
# Note that ContentEditor above was a Enable because it's about visualization (canvas)
# but ButtonEditor is a TraitsUI instance.

# When button is clicked _open_file_fired will be fired.
# _open_file_fired opens a dialog with FileDialog() (comes from pyface.api).
# FileDialog returns selected file path.
# drill_data changes when the file is read.

# Confused by ChannelsView's logic....
# Facts:
# - selected_channels is no more than a List.
# - channels is a property depends on drill_data
#   (you can call channels but no static data! It's kind of a function!)
# - channels_view is a property depends on selected_channels
#   (again, channels_view a function! Thus you want @chaced_property)

class DataView(HasStrictTraits):
    drill_data = Instance(DrillData) # data
    filename = Str() # data
    open_file = Event() # data
    channels = Property(depends_on="drill_data") # NOT DATA!
    selected_channels = List() # data
    channels_view = Property(Instance(ChannelsView), depends_on="selected_channels") # NOT DATA!

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