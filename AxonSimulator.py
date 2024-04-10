from neuron import h
import numpy as np
import plotly.graph_objects as go
import math
import plotly

h.load_file("stdrun.hoc")

#preparing axon
n_sections = 9  #set the amount of sections
membrane_area = []

#interval in ms
h.dt = 0.0001

#creating 2 types of sections (Myelin Sheeted and Ranvier) in a quantitive ratio of 1:1
axon = []   #makes an empty list that can hold the sections respectively
for i  in range(n_sections):
    if i % 2 == 0:  #all even numbers are with Myelin
        axon.append(h.Section(name = f"Section {i}M"))
        h.hh.insert(axon[i])

        axon[i].L = 2000
        axon[i].diam = 10
        axon[i].Ra = 0.1
        axon[i].cm = 0.005

        # 0.0000015 siemens total

        axon[i](0.5).hh.gnabar = 1.15163148e-6   #1.15163148e-6     #Sodium conductance  (S/mc^2)  default: 0.12           0.76775431861804222648752399232246 %
        axon[i](0.5).hh.gkbar = 3.45489443e-7  #3.45489443e-7    #Potassium   default: 0.036                            0.23032629558541266794625719769674 %
        axon[i](0.5).hh.gl = 2.87907869e-9     #2.87907869e-9       #leak    default: 0.0003                               0.00191938579654510556621880998081 %
        axon[i](0.5).hh.el = -54.3        #leak reversal potential (mV) leak channel

        membrane_area.append([(math.pi) * (axon[i].diam ** 2) * (axon[i].L)])

        if i > 0:
            axon[i-1].connect(axon[i](1))

    else:  #all odd numbers are Ranviers
        axon.append(h.Section(name = f"Section {i}R"))
        h.hh.insert(axon[i])
        axon[i].L = 3.183
        axon[i].diam = 6
        axon[i].Ra = 0.1
        axon[i].cm = 0.000001

        axon[i](0.5).hh.gnabar = 1.2
        axon[i](0.5).hh.gkbar = 0.36
        axon[i](0.5).hh.gl = 0.003
        axon[i](0.5).hh.el = -54.3

        membrane_area.append([(math.pi) * (axon[i].diam ** 2) * (axon[i].L)])

        axon[i-1].connect(axon[i](1))

# Create a stimulating clamp at normalized position 0 of the first axon section
ic = h.IClamp(axon[0](0))     #places the stimulus clamp on the normalized position 0.5 of the section "axon" (0 is the begining of the length and 1 is the end of the lenght)
ic.delay = 5                 # delay stimulus     (in ms)
ic.dur = 0.05                 # duration stimulus  (in ms)
ic.amp = 10                   # amplitude stimulus (in nanoAmps)

# Record time
t = h.Vector().record(h._ref_t)    #records the passage of time in the variable "t"

# Record membrane potential for each segment
v_vectors = []    #creates a list of hoc.Vectors where the number of items in the list is the number of sections for "axon" (n_sections)    (a list stores itmes like so: ["shoe", 4, 6.5, Vector [184]])

#make a loop to measure membrane potential (mV) for the center point of each section and store it in the previously created list "v_vectors"
for i in range(n_sections):
    v_vectors.append(h.Vector().record(axon[i](0.5)._ref_v))      #this will be executed "n_sections"-number of times and the value i increases by 1 every time, corresponding to the "n_sections"-number of items in the list "v_vectors" and adding a recoreded mV value at each position as a Vector

# Record ion currents
ina = []
ik = []
il = []
icap = []

for i in range(n_sections):
    ina.append((h.Vector().record(axon[i](0.5)._ref_ina)))        #vector for sodium channel

    ik.append((h.Vector().record(axon[i](0.5)._ref_ik)))          #vector for potassium channel
    il.append((h.Vector().record(axon[i](0.5).hh._ref_il)))       #vector for l channel
    icap.append((h.Vector().record(axon[i](0.5)._ref_i_cap)))     #vector for cap channel

# Set parameters and run the simulation

h.celsius = 18.5
h.finitialize(-65)  # defining the baseline membrane potential (in mV)
h.continuerun(10)    # duration of the simulation (in ms)

# Convert the vectors to NumPy arrays
t_np = np.array(t)                                            #converts the hoc.Vector of "t" to a numpy array
v_np = np.array([vec.as_numpy() for vec in v_vectors])        #converts the list "v_vectors" of hoc.Vector items to a list with numpy array items

# Calculate the mean membrane potential
mean_v = np.mean(v_np, axis=0)                                #calculates and stores the mean value of all the numpy vectors from each recorded segment of "axon"

# Calculate the sum of the currents
itot_np = []
idens_np = []

for i in range(n_sections):
    itot_np.append(np.array(ina[i]) + np.array(ik[i]) + np.array(il[i]) + np.array(icap[i]))  #numpy array sum of ion channel currants
    idens_np.append((np.array(ina[i]) / membrane_area[i]) + (np.array(ik[i]) / membrane_area[i]) + (np.array(il[i]) / membrane_area[i]) + (np.array(icap[i]) / membrane_area[i]))


#Mean I for myelinated and Ranvier
Myelin = []
Ranvier = []
names = ["Myelinated", "Nodes of Ranvier"]

for i in range(n_sections):
    if i % 2 == 0:
        Myelin.append(itot_np[i])
    else:
        Ranvier.append(itot_np[i])

itot_mean = [np.mean(Myelin, axis = 0), np.mean(Ranvier, axis = 0)]

#mean of each ion channel
imean_np = [np.mean(ina, axis=0), np.mean(ik, axis=0), np.mean(il, axis=0), np.mean(icap, axis=0)]

colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22"]

# Create scatter plots
fig_itot_mean = go.Figure(data=[go.Scatter(x=t_np, y=itot_mean[i], mode='lines',name = names[i]) for i in range(2)])                                                          #creates figure of currant sum over time
fig_itot_mean.update_layout(title='Total Current Over Time', xaxis_title='Time (ms)', yaxis_title='Total Current (nA)')
plotly.offline.plot(fig_itot_mean)

fig_itot = go.Figure(data=[go.Scatter(x=t_np, y=itot_np[i], mode='lines',name = axon[i].name()) for i in range(n_sections)])                                                          #creates figure of currant sum over time
fig_itot.update_layout(title='Total Current Over Time per Section', xaxis_title='Time (ms)', yaxis_title='Total Current (nA)')
fig_itot.show() ##plotting online (if all are plottet online or offline there is some bug with plotly where a seemingly random plot doesnt generate)

fig_mean_v = go.Figure(data=go.Scatter(x=t_np, y=mean_v, mode='lines'))                                                                  #creates figure of mean membrane potential over time
fig_mean_v.update_layout(title='Mean Membrane Potential Over Time', xaxis_title='Time (ms)', yaxis_title='Mean Membrane Potential (mV)')
plotly.offline.plot(fig_mean_v)

fig_v = go.Figure(data=[go.Scatter(x=t_np, y=v_np[i], mode='lines', name = axon[i].name()) for i in range(n_sections)])                                        #creates figure with each segments membrane potential over time
fig_v.update_layout(title='Membrane Potential Over Time per Section', xaxis_title='Time (ms)', yaxis_title='Membrane Potential (mV)')
plotly.offline.plot(fig_v)
