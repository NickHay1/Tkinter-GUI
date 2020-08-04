import geopandas as gpd
import pandas as pd
import cartopy.crs
import pyproj
import geoplot as gplt
import geoplot.crs
import contextily as ctxt
from matplotlib import pyplot as plt
import matplotlib.patheffects as pe
import tkinter as tk
from matplotlib.backends.backend_tkagg import *
from pyproj import Proj, transform
import mapclassify as mc
from matplotlib.patches import Patch
import matplotlib
import matplotlib_scalebar
from matplotlib_scalebar.scalebar import ScaleBar, SI_LENGTH
from PIL import Image, ImageTk
import matplotlib.colors as clr
from fuzzywuzzy import fuzz

la_name = 'Adur'
dpi = 95
export_dpi = 200

############################
#Data
############################
#Wards
wards = gpd.read_file(
	r'FilePath', 
	layer='Wards'
)
wards = wards.loc[wards['LAD11NM'] == la_name].to_crs(epsg=4326)

#COAs
coas = gpd.read_file(
	r'FilePath', 
	layer='COAs'
)
data = pd.read_csv(r'FilePath')
coas = pd.merge(
	left=coas, right=data, left_on='OA11CD', right_on='COACode'
).to_crs(epsg=4326)
pr_data = pd.read_csv(r'FilePath')
coas = pd.merge(
	left=coas, right=pr_data, left_on='OA11CD', right_on='COACode'
)

############################
#Plot
############################
figure, ax = plt.subplots(
	1, 1, figsize=(12, 9), dpi=dpi, 
	subplot_kw={'projection': cartopy.crs.epsg(3857), 'picker': True}
)
plt.tight_layout(pad=0, h_pad=0, w_pad=0)

#Convert Bounds to Aspect Ratio
def to_aspect():
	#Exsisting Bounds
	bounds_ = list(wards.total_bounds)
	bounds = [
		i - 0.003 if i == bounds_[0] or i == bounds_[1] else i + 0.003 for i in bounds_
	]
	x0, y0  = transform(
		Proj(init='epsg:4326'), Proj(init='epsg:3857'), 
		bounds[0], bounds[1]
	)
	x1, y1 = transform(
		Proj(init='epsg:4326'), Proj(init='epsg:3857'), 
		bounds[2], bounds[3]
	)
	#New Bounds
	width = x1 - x0
	height = y1 - y0
	if width < height:
		x_lim = height * 1.333
		y_lim = height
	elif width > height: 
		x_lim = width 
		y_lim = width / 1.333
		if y_lim < height:
			x_lim = width * 1.333
			y_lim = width
	mid_x = (x0 + x1) / 2
	mid_y = (y0 + y1) / 2

	return [
		mid_x - x_lim/2, mid_y - y_lim/2,
		mid_x + x_lim/2, mid_y + y_lim/2
	]

############################
#Plot Elements
############################
#Plot Wards
gplt.polyplot(
	wards, ax=ax, projection=geoplot.crs.WebMercator(), zorder=2, linewidth=2, 
)
#Reference to ward features
ward_list = []
for x in ax.get_children():
	if type(x) == cartopy.mpl.feature_artist.FeatureArtist:
		ward_list.append(x)

#Axis Limits 
bounds = to_aspect()
ax.set_xlim(left=bounds[0], right=bounds[2])
ax.set_ylim(bottom=bounds[1], top=bounds[3])

#Basemap
def add_basemap():
	ctxt.add_basemap(ax=ax, url=ctxt.providers.CartoDB.Voyager)
add_basemap()

#New df for Labels
wards_labels = wards.to_crs(epsg=3857)
wards_labels['coords'] = wards_labels['geometry'].apply(
	lambda column: [column.centroid.x, column.centroid.y] 
)
#Create Labels and save reference to these labels
label_list = []
for index, row in wards_labels.iterrows():
	label = plt.text(
		s=row['Ward_ID'], x=row['coords'][0], y=row['coords'][1], horizontalalignment='center', 
		fontsize=14, path_effects=[pe.withStroke(linewidth=6, foreground='w')], zorder=3, 
		picker=True
	)
	label_list.append(label)

############################
#COA Elements
############################
#Choropleth Colors 
def gen_cmap(n, hex1, hex2, hex3, hex4, hex5):
	return clr.LinearSegmentedColormap.from_list(
		n, [(0, hex1), (.25, hex2), (.5, hex3), (.75, hex4), (1, hex5)], 
		N=256
	)

choro_list = [
	gen_cmap(n='pcHHSRS', hex1='#ffffdd', hex2='#ffd799', hex3='#f29d52', hex4='#c06e46', hex5='#a66141'), 
	gen_cmap(n='pcExcessCold', hex1='#f4f2f7', hex2='#ccd4e7', hex3='#97bfdb', hex4='#60aacf', hex5='#4383a7'), 
	gen_cmap(n='pcHHSRSFalls', hex1='#fff2ec', hex2='#f9c5ca', hex3='#fa8eb8', hex4='#d454a7', hex5='#9b4199'), 
	gen_cmap(n='pcDisrepair', hex1='#fafafa', hex2='#d9d9d9', hex3='#b0b0b0', hex4='#8a8a8a', hex5='#5c5c5c'), 
	gen_cmap(n='pcFP10', hex1='#fff3e3', hex2='#fcd8a8', hex3='#fca981', hex4='#eb7865', hex5='#c6403f'), 
	gen_cmap(n='pcFPLIHC', hex1='#faf5fb', hex2='#d3d6e9', hex3='#e6b1c3', hex4='#e68a97', hex5='#b35273'), 
	gen_cmap(n='pcLowIncome', hex1='#ffffd9', hex2='#d4edb4', hex3='#9cd69d', hex4='#65ba7e', hex5='#418e6a'), 
	gen_cmap(n='pcECLI', hex1='#feffd8', hex2='#b8e3c5', hex3='#72cad6', hex4='#61a0c9', hex5='#5e68b0'), 
	gen_cmap(n='pcEPCFG', hex1='#e1f5f3', hex2='#b7d4cf', hex3='#8eb4ad', hex4='#6f9693', hex5='#4f7a76'), 
	gen_cmap(n='pcSolidWall', hex1='#ebdff5', hex2='#cfbadb', hex3='#b599c2', hex4='#9b7ca8', hex5='#866194'), 
	gen_cmap(n='pcInsCavity', hex1='#ebdff5', hex2='#cfbadb', hex3='#b599c2', hex4='#9b7ca8', hex5='#866194'), 
	gen_cmap(n='pcUninsCavity', hex1='#ebdff5', hex2='#cfbadb', hex3='#b599c2', hex4='#9b7ca8', hex5='#866194'), 
	gen_cmap(n='pcLInsLT100', hex1='#ffffff', hex2='#fee6e6', hex3='#ffcfcf', hex4='#f9a487', hex5='#ed7a41'), 
	gen_cmap(n='SimpleCO2', hex1='#fff0e0', hex2='#f6ceb5', hex3='#e8a18b', hex4='#dd7667', hex5='#d44847'), 
	gen_cmap(n='HeatDemand', hex1='#ffffff', hex2='#fee6e6', hex3='#ffcfcf', hex4='#f9a487', hex5='#ed7a41'), 
	gen_cmap(n='HeatCost', hex1='#ffd8d9', hex2='#ffb7ab', hex3='#f99482', hex4='#f17261', hex5='#e3413f'), 
	gen_cmap(n='EnergyDemand', hex1='#ffffd9', hex2='#d4edb4', hex3='#9cd59e', hex4='#65bb7e', hex5='#418e6a'), 
	gen_cmap(n='EnergyCost', hex1='#e1f5f3', hex2='#b7d4cf', hex3='#8fb4ad', hex4='#6f9693', hex5='#507a76'), 
	gen_cmap(n='ElectricityDemand', hex1='#ffffff', hex2='#b2cef5', hex3='#57a1e8', hex4='#5772c9', hex5='#4847ad'), 
	gen_cmap(n='ElectricityCost', hex1='#ffffff', hex2='#b2cef5', hex3='#57a1e8', hex4='#5772c9', hex5='#4847ad'), 
	gen_cmap(n='SimpleSAP', hex1='#418f81', hex2='#53acb2', hex3='#8cbddb', hex4='#ccd4e7', hex5='#faf5fb'), 
	gen_cmap(n='pcPrivateRentedModel', hex1='#ffffff', hex2='#f5e6fb', hex3='#ebcaf9', hex4='#e3b4fa', hex5='#d699f8'), 
	gen_cmap(n='pc2011CensusPR', hex1='#ffffff', hex2='#ffe6f1', hex3='#fccce2', hex4='#fab4d6', hex5='#f699c6')
]

for cmap in choro_list:
	plt.register_cmap(cmap=cmap)

#Legend Title
def gen_title(ind, **kwargs):
	if 'unit' in kwargs:
		str_ =  r"\textbf{{{0}}}".format('Private Rented') + \
				'\n{0}\n{1} and (no. of COAs)'.format(ind, kwargs['unit'])
	else:
		str_ = r"\textbf{{{0}}}".format('Private Rented') + \
				'\n{0}\nPercent and (no. of COAs)'.format(ind) 

	return str_

ldict = {
	'pcHHSRS': gen_title(ind='HHSRS Cat. 1 Hazards'), 'pcExcessCold': gen_title(ind='HHSRS Excess Cold'), 
	'pcHHSRSFalls': gen_title(ind='HHSRS Falls Hazards'), 'pcDisrepair': gen_title(ind='Disrepair'), 
	'pcFP10': gen_title(ind='Fuel Poverty 10%'), 'pcFPLIHC': gen_title(ind='Fuel Poverty LIHC'),
	'pcLowIncome': gen_title(ind='Low Income Households'), 'pcECLI': gen_title(ind='Excess Cold and Low Income'), 
	'pcEPCFG': gen_title(ind='EPC Rating F or G'), 'pcSolidWall': gen_title(ind='Solid Walls'), 
	'pcInsCavity': gen_title(ind='Insulated Cavity Walls'), 'pcUninsCavity': gen_title(ind='Un-Insulated Cavity Walls'), 
	'pcLInsLT100': gen_title(ind='Loft Insulation less than 100mm'), 'SimpleCO2': gen_title(ind='Average SimpleCO2', unit='Tonnes/year'), 
	'HeatDemand': gen_title(ind='Average Total Heat Demand', unit='kWh/year'), 'HeatCost': gen_title(ind='Average Total Heat Cost', unit='£/year'), 
	'EnergyDemand': gen_title(ind='Average Total Energy Demand', unit='kWh/year'), 'EnergyCost': gen_title(ind='Average Total Energy Cost', unit='£/year'), 
	'ElectricityDemand': gen_title(ind='Average Total Electricity Demand', unit='kWh/year'), 'ElectricityCost': gen_title(ind='Average Total Electricity Cost', unit='£/year'), 
	'SimpleSAP': gen_title(ind='Average SimpleSAP', unit='Score'), 'pcPrivateRentedModel': gen_title(ind='Private Rented (BRE Model)'), 
	'pc2011CensusPR': gen_title(ind='Private Rented (Census 2011)')
}
get_title = lambda option: ldict.setdefault(option)
matplotlib.rc('text', usetex=True) #allows Latex format
#Latex Text Formatting 
plt.rcParams['text.latex.preamble'] = r'''
\usepackage{mathtools}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
'''

#COA Layer
def add_coa(option):
	#Get Bounds 
	x0, x1 = ax.get_xlim()
	y0, y1 = ax.get_ylim()

	#Plot COA
	gplt.choropleth(
		coas, ax=ax, projection=geoplot.crs.WebMercator(), hue=option, 
		zorder=1, alpha=0.7, scheme=mc.NaturalBreaks(coas[option], k=5), 
		cmap=option, legend=False, edgecolor='lightgray'
	)
	#Set Extent
	ax.set_xlim(left=x0, right=x1)
	ax.set_ylim(bottom=y0, top=y1)

#Legend
def add_legend(option):
	#Decide Format
	if option == 'SimpleCO2': frmt = '{:.1f}'
	else: frmt = '{:.0f}'

	#Legend Labels
	classification = mc.NaturalBreaks(coas[option], k=5)
	legend_labels = []
	for i, c in enumerate(classification.counts):
		if i == 0:
			str_ = "{0} - {1}".format(
				str(frmt.format(coas[option].min())), str(frmt.format(classification.bins[i]))
			)
		else:
			str_ = "{0} - {1}".format(
				str(frmt.format(classification.bins[i-1])), str(frmt.format(classification.bins[i]))
			)
		str_ += "({0})".format(c)
		legend_labels.append(str_)
	#Legend Handles
	cmap = matplotlib.cm.get_cmap(option)
	handles = [
		Patch(edgecolor='black', facecolor=cmap(0.)), 
		Patch(edgecolor='black', facecolor=cmap(.25)), 
		Patch(edgecolor='black', facecolor=cmap(.5)), 
		Patch(edgecolor='black', facecolor=cmap(.75)), 
		Patch(edgecolor='black', facecolor=cmap(1.))
	]

	#Create Legend
	legend = ax.legend(
		handles=handles, labels=legend_labels, loc='upper left', title=get_title(option), 
		framealpha=1, facecolor='white', edgecolor='black', fancybox=False, handlelength=1
	)
	legend._legend_box.align = 'left' #align text 
	#Make Draggable
	legend.set_draggable(True, update='loc')

#COA Operations 
def coa_operations(option):
	#Create COA Artists reference 
	coa_list = [
		x for x in ax.get_children() if type(x) == cartopy.mpl.feature_artist.FeatureArtist \
		and x not in ward_list
	] 
	#reference to layer
	global layer_ref 
	layer_ref = option

	if option == '--No Layer--':
		legend = [
			x for x in ax.get_children() if type(x) == matplotlib.legend.Legend
		][0] #Legend reference 
		for x in coa_list: x.remove()
		legend.remove()
		canvas.draw()
	else:
		for x in coa_list: x.remove()
		add_coa(option)
		add_legend(option)
		canvas.draw()

############################
#Ancilliary Plot Elements
############################
#Attribute Table
table_data = wards.loc[:, ['Ward_ID', 'WardName']]
table_data = table_data.rename(
	columns={'Ward_ID': 'Ward ID', 'WardName': 'Ward Name'}
).sort_values(by='Ward ID', ascending=True)

#Draw Table
table = ax.table(
	cellText=table_data.values, zorder=4, cellLoc='left', 
	loc='lower left', colLoc='left', picker=True,
	colLabels=[ 
		r"\textbf{{{0}}}".format(table_data.columns[0]), 
		r"\textbf{{{0}}}".format(table_data.columns[1])
	]	
)
table.auto_set_font_size(False)
table.auto_set_column_width(col=list(range(len(table_data.columns))))
table.set_fontsize(8)
#Adjust Column Padding
cells = [key for key in table._cells if key[1] == 1]
for cell in cells: table._cells[cell].PAD = 0.04
cells = [key for key in table._cells if key[1] == 0]
for cell in cells: table._cells[cell].PAD = 0.04

table.set_visible(True) #set default not visible

#Scalebar
distance_format = lambda value, unit: '{0:.2f}'.format(value)
scalebar = ScaleBar(
	dx=0.001, units='km', dimension=SI_LENGTH, location='lower center', label='km', 
	label_loc='right', frameon=False, sep=3, length_fraction=0.35, label_formatter=distance_format
)
#Add Scalebar
ax.add_artist(scalebar)
scalebar = [x for x in ax.get_children() \
			if type(x) == matplotlib_scalebar.scalebar.ScaleBar]
scalebar[0].set_visible(True) #default not visible

############################
#Tkinter GUI
############################
root = tk.Tk()
window = tk.Toplevel(master=root)

frame = tk.Frame(master=window, bd=1, background='BLACK')
frame.grid(column=0, row=0, columnspan=10)

canvas = FigureCanvasTkAgg(figure, master=frame)
canvas.get_tk_widget().pack()

#COA Layer Options
tk.Label(window, text='--Layer Options--', font='Helvetica 9 bold').grid(column=0, row=1)

coa_options = [
	'--No Layer--', 'pcHHSRS', 'pcExcessCold', 'pcHHSRSFalls', 'pcDisrepair', 'pcFP10', 'pcFPLIHC', 'pcLowIncome', 
	'pcECLI', 'pcEPCFG', 'pcSolidWall', 'pcInsCavity', 'pcUninsCavity', 'pcLInsLT100', 'SimpleCO2', 'HeatDemand', 
	'HeatCost', 'EnergyDemand', 'EnergyCost', 'ElectricityDemand', 'ElectricityCost', 'SimpleSAP', 'pcPrivateRentedModel',
	'pc2011CensusPR' 
]
coa_init = tk.StringVar()
coa_init.set(coa_options[0])
coa_dropdown = tk.OptionMenu(window, coa_init, *coa_options, command=coa_operations)
coa_dropdown.grid(column=0, row=2)

############################
#TK Imagery
############################
def tk_image(url, width_, *args):
	#Resize image whilst preserving aspect
	image = Image.open(url)
	width, height = image.size
	new_width = width_ 
	new_height = round((height / width) * new_width)
	image = image.resize((new_width, new_height))

	#For RGBA Images
	if 'alpha' in args: image = image.convert('RGBA')

	#Return PIL and TK Image Objects
	return ImageTk.PhotoImage(image), image

#Images 
logo_tk, logo_pil = tk_image(url=r'FilePath', width_=100)
arrow_tk, arrow_pil = tk_image(r'FilePath', 65, 'alpha')

#Labels
logo_label = tk.Label(master=frame, image=logo_tk)
logo_label.image = logo_tk
logo_label.place(x=0, y=0)
arrow_label = tk.Label(master=frame, image=arrow_tk, bg='white')
arrow_label.image = arrow_tk
arrow_label.place(x=0, y=0)

#Update Label Positioning 
root.update()
logo_label.place(
	x = frame.winfo_width() - logo_label.winfo_width() - 5, 
	y = frame.winfo_height() - logo_label.winfo_height() - 5
)
arrow_label.place(
	x = frame.winfo_width() - arrow_label.winfo_width() - 5, 
	y = 5 
)
root.update()

#Make Images Draggable
def im_drag_start(event):
	widget = event.widget
	widget.drag_start_x = event.x
	widget.drag_start_y = event.y

def im_drag_motion(event):
	widget = event.widget
	x = widget.winfo_x() - widget.drag_start_x + event.x
	y = widget.winfo_y() - widget.drag_start_y + event.y
	widget.place(x=x, y=y)

logo_label.bind("<Button-1>", im_drag_start)
logo_label.bind("<B1-Motion>", im_drag_motion)

arrow_label.bind("<Button-1>", im_drag_start)
arrow_label.bind("<B1-Motion>", im_drag_motion)

############################
#Matplotlib Functionality
############################
#Artist Visibility
class PltToggle:

	def __init__(self, artist, init):
		self.artist = artist 
		self.init = init

	def visibility_toggle(self):
		if self.init.get() == 'on':
			self.artist.set_visible(True)
			canvas.draw()
		elif self.init.get() == 'off':
			self.artist.set_visible(False)
			canvas.draw()

table_status = tk.StringVar()
table_visibility = PltToggle(artist=table, init=table_status)
table_toggle = tk.Checkbutton(
	window, text='Attribute Table', variable=table_status, onvalue='on',
	offvalue='off', command=table_visibility.visibility_toggle
)
table_toggle.select()
table_toggle.grid(column=1, row=2)

sb_status = tk.StringVar()
sb_visibility = PltToggle(artist=scalebar[0], init=sb_status)
sb_toggle = tk.Checkbutton(
	window, text='Scalebar', variable=sb_status, onvalue='on',
	offvalue='off', command=sb_visibility.visibility_toggle	
)
sb_toggle.select()
sb_toggle.grid(column=1, row=3)

tk.Label(window, text='--Ancilliary Elements--', font='Helvetica 9 bold').grid(row=1, column=1)

#Make Labels Draggable
class DraggableLabel:

	def __init__(self, label):
		self.label = label
		self.txt_press = None
		self.txt_drag_init()

	def txt_drag_press(self, event):
		if event.artist != self.label: return
		if event.mouseevent.button == 1:
			x0, y0 = self.label.get_position()
			self.txt_press = event.mouseevent.x, event.mouseevent.y, x0, y0

	def txt_drag_motion(self, event):
		if self.txt_press != None:
			mouse_x, mouse_y, x0, y0 = self.txt_press
			dx = event.x - mouse_x
			dy = event.y - mouse_y
			self.label.set_position((x0 + dx, y0 + dy))
			canvas.draw()

	def txt_drag_release(self, event):
		self.txt_press = None

	def txt_drag_init(self):
		self.cid1 = self.label.figure.canvas.mpl_connect('pick_event', self.txt_drag_press)
		self.cid2 = self.label.figure.canvas.mpl_connect('motion_notify_event', self.txt_drag_motion)
		self.cid3 = self.label.figure.canvas.mpl_connect('button_release_event', self.txt_drag_release)

dls = []
for label in label_list:
	dl = DraggableLabel(label)
	dls.append(dl)

#Draggable Extent
class DraggableExtent:

	def __init__(self):
		self.press = None

	def extent_drag_press(self, event):
		if event.mouseevent.button == 1:
			self.x0, self.x1 = ax.get_xlim()
			self.y0, self.y1 = ax.get_ylim()
			self.width = self.x1 - self.x0 
			self.height = self. y1 - self.y0
			self.press = event.mouseevent.x, event.mouseevent.y

	def extent_drag_motion(self, event):
		if self.press != None:
			mouse_x, mouse_y = self.press
			dx = event.x - mouse_x
			dy = event.y - mouse_y
			x0 = self.x0 + (-dx*3) 
			y0 = self.y0 + (-dy*3)
			ax.set_xlim(
				left=x0, right=x0 + self.width
			) 
			ax.set_ylim(
				bottom=y0, top=y0 + self.height
			)
			
			canvas.draw()

	def extent_drag_release(self, event):
		self.press = None
		add_basemap()
		canvas.draw()

	def extent_drag_init(self):
		if extent_status.get() == 'on':
			self.cid1 = ax.figure.canvas.mpl_connect('pick_event', self.extent_drag_press)
			self.cid2 = ax.figure.canvas.mpl_connect('motion_notify_event', self.extent_drag_motion)
			self.cid3 = ax.figure.canvas.mpl_connect('button_release_event', self.extent_drag_release)
		elif extent_status.get() == 'off':
			ax.figure.canvas.mpl_disconnect(self.cid1)
			ax.figure.canvas.mpl_disconnect(self.cid2)
			ax.figure.canvas.mpl_disconnect(self.cid3)

extent_status = tk.StringVar()
extent_drag = DraggableExtent()
extent_toggle = tk.Checkbutton(
	window, text='Map Extent Toggle', variable=extent_status, onvalue='on', 
	offvalue='off', command=extent_drag.extent_drag_init
)
extent_toggle.deselect()
extent_toggle.grid(column=2, row=2)

tk.Label(window, text='--Map View--', font='Helvetica 9 bold').grid(column=2, row=1)

#Mousewheel Extent Control
def extent_control(event):
	if extent_status.get() == 'off': return

	x0, x1 = ax.get_xlim()
	y0, y1 = ax.get_ylim()
	sf = (y1 - y0)/(x1 - x0)
	#Change limits whilst preserving aspect
	if event.delta > 0: 
		x_lim = [x0 + 300, x1 - 300]
		y_lim = [y0 + (300*sf), y1 - (300*sf)]
	if event.delta < 0:
		x_lim = [x0 - 300, x1 + 300]
		y_lim = [y0 - (300*sf), y1 + (300*sf)]
		
	#Set Limits
	ax.set_xlim(left=x_lim[0], right=x_lim[1])
	ax.set_ylim(bottom=y_lim[0], top=y_lim[1])
	add_basemap()
	canvas.draw()

window.bind("<MouseWheel>", extent_control)

#Make Table Draggable
class DraggableTable:

	def __init__(self):
		self.press = None
		self.plt_drag_init()

	def plt_drag_press(self, event):
		#Make sure Table is picked 
		if event.artist != table: return 
		if event.mouseevent.button == 1:
			#Get coordinates of table upon press event
			bbox = table.get_window_extent(renderer=figure.canvas.renderer)
			self.press = bbox.x0, bbox.y0, event.mouseevent.x, event.mouseevent.y
			self.dimensions = bbox.width, bbox.height

	def plt_drag_motion(self, event):
		if self.press != None:
			#Calculate new coordinates and convert to axes units
			x0, y0, mouse_x, mouse_y = self.press
			width, height = self.dimensions
			dx = event.x - mouse_x
			dy = event.y - mouse_y
			loc_in_axes = ax.transAxes.inverted().transform(
				[(x0 + dx, y0 + dy), (width, height)]
			)
			loc_in_axes = [i for element in loc_in_axes for i in element]
			table._bbox = loc_in_axes
			canvas.draw()

	def plt_drag_release(self, event):
		self.press = None

	def plt_drag_init(self):
		table.figure.canvas.mpl_connect('pick_event', self.plt_drag_press)
		table.figure.canvas.mpl_connect('motion_notify_event', self.plt_drag_motion)
		table.figure.canvas.mpl_connect('button_release_event', self.plt_drag_release)

dt = DraggableTable()

#Change Scalebar Position 
def sb_loc(option):
	scalebar[0]._location = option
	canvas.draw()

loc_init = tk.StringVar()
loc_init.set('lower center')
loc_options = [
	'upper right', 'upper left', 'lower left', 'lower right', 
	'right', 'center left', 'center right', 'lower center', 'upper center', 
	'center'
]
loc_dropdown = tk.OptionMenu(window, loc_init, *loc_options, command=sb_loc)
loc_dropdown.grid(column=1, row=4)

############################
#Exporting
############################
#Create Fig Image Instances
def tk_to_plt(label, image):
	#Tk Coords to Plt
	x = label.winfo_x()
	y = frame.winfo_height() - label.winfo_y()
	offset_y = y - label.winfo_height()

	if export_dpi == dpi:
		return plt.figimage(
			image, xo=x, yo=offset_y, origin='upper'
		)
	
	#Else adjust for export dpi
	width_, height_ = image.size 
	sf = export_dpi/dpi
	width = round(width_ * sf)
	height = round((height_/width_) * width)
	x *= sf 
	offset_y *= sf

	return plt.figimage(
		image.resize((width, height)), xo=x, yo=offset_y, 
		origin='upper'
	)

def export(*args):
	#Create Figure Images
	logo_plt = tk_to_plt(label=logo_label, image=logo_pil)
	arrow_plt = tk_to_plt(label=arrow_label, image=arrow_pil)

	if 'single' in args: #export single layer
		plt.savefig(
			r'FilePath'.format(layer_ref), dpi=export_dpi
		)
		logo_plt.remove()
		arrow_plt.remove()
	elif 'all' in args: #export all layers
		for column in coa_options:
			#Perform Ops
			coa_operations(column)
			#Save Layer
			plt.savefig(
				r'FilePath'.format(column), dpi=export_dpi
			)
		#Remove FigImage Instances
		logo_plt.remove()
		arrow_plt.remove()

#Export 
outfile_single = tk.Button(master=window, text='Export Current Layer', command=lambda: export('single'))
outfile_single.grid(column=3, row=2)
outfile_all = tk.Button(master=window, text='Export All Layers', command=lambda: export('all'))
outfile_all.grid(column=3, row=3)

tk.Label(window, text='--Export--', font='Helvetica 9 bold').grid(column=3, row=1)

tk.mainloop()




