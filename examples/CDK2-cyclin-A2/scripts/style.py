import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
SURF='#fcfcfb'; INK='#0b0b0b'; INK2='#52514e'; MUTED='#898781'
GRID='#e1e0d9'; AXIS='#c3c2b7'
CAT=['#2a78d6','#eb6834','#1baf7a','#eda100','#e87ba4','#008300','#4a3aa7','#e34948']
BLUE=['#cde2fb','#b7d3f6','#9ec5f4','#86b6ef','#6da7ec','#5598e7','#3987e5','#2a78d6','#256abf','#1c5cab','#184f95','#104281','#0d366b']
SEQ=LinearSegmentedColormap.from_list('bdbblue',BLUE)
MARKERS=['o','s','^','D','v','P','X','<','>','p','h','*']
plt.rcParams.update({
 'font.family':'sans-serif','font.sans-serif':['DejaVu Sans'],'font.size':9,
 'figure.facecolor':SURF,'axes.facecolor':SURF,'savefig.facecolor':SURF,
 'axes.edgecolor':AXIS,'axes.labelcolor':INK2,'text.color':INK,
 'xtick.color':MUTED,'ytick.color':MUTED,'xtick.labelsize':8,'ytick.labelsize':8,
 'axes.grid':True,'grid.color':GRID,'grid.linewidth':0.6,'axes.axisbelow':True,
 'axes.spines.top':False,'axes.spines.right':False,'legend.frameon':False,
 'axes.titlesize':10,'axes.titleweight':'bold','axes.titlelocation':'left',
 'lines.linewidth':2,'figure.dpi':200,
})
def order_chemotypes(df):
    return list(df.chemotype.value_counts().index)
def ct_style(order):
    return {c:(CAT[i%8],MARKERS[i%12]) for i,c in enumerate(order)}
