#!pip install pymoo
import pandas as pd
import numpy as np
import math
import json
from pymoo.indicators.hv import HV
import statistics

# Cargar datos desde archivo JSON
with open('resultados.json', 'r') as archivo_json:
    datos = json.load(archivo_json)

# Acceder a las variables
FO1_values = datos['FO1_values']
FO2_values = datos['FO2_values']
FO3_values = datos['FO3_values']
refugios = datos["refugios"]
Ev_values = datos['Ev_values']
R_values = datos['R_values']
ec1_values = datos['ec1_values']
ec2_values = datos['ec2_values']
infactible_ec1 = datos['infactible_ec1']
infactible_ec2 = datos['infactible_ec2']
debiles_ec1 = datos['debiles_ec1']
debiles_ec2 = datos['debiles_ec2']
dis_ref_values = datos['dis_ref_values']
Ev_Ref_values = datos['Ev_Ref_values']
D_prom_values = datos['D_prom_values']
elapsed_time =  datos['Elapsed_time']
zonas_demanda = datos["zonas_demanda"]

# Convertir los valores a un range nuevamente
refugios = range(datos["refugios"]["start"], datos["refugios"]["stop"], datos["refugios"]["step"])
zonas_demanda = range(datos["zonas_demanda"]["start"], datos["zonas_demanda"]["stop"], datos["zonas_demanda"]["step"])

print("Datos cargados correctamente desde JSON.")

A=np.vstack((FO1_values,FO2_values,FO3_values)).T
AA=pd.DataFrame(A, columns =['FO1', 'FO2', 'FO3'])

min_FO1=AA['FO1'].min()
min_FO2=AA['FO2'].min()
min_FO3=AA['FO3'].min()
max_FO1=AA['FO1'].max()
max_FO2=AA['FO2'].max()
max_FO3=AA['FO3'].max()
AA['FO1']=(AA['FO1']-min_FO1)/(max_FO1-min_FO1)
AA['FO2']=(AA['FO2']-min_FO2)/(max_FO2-min_FO2)
AA['FO3']=(AA['FO3']-min_FO3)/(max_FO3-min_FO3)
A=AA.values

# ONVG
ONVG=A.shape[0]

## HV
ref_point = np.array([1,1,1])
ind = HV(ref_point=ref_point)
HVOL=ind(A)

## 
kd_values =[]
valores_p=[]
valores_q=[]
pit=np.linspace(0,len(A)-1, ONVG)
pit2=np.linspace(0,len(A)-1, ONVG)
q=0
for p in pit:
  p=int(p)
  for q in pit2:
    q=int(q)
    kd=math.sqrt((A[q,0]-A[p,0])**2+(A[q,1]-A[p,1])**2+(A[q,2]-A[p,2])**2)
    if kd!=0:
      kd_values.append(kd)
      valores_p.append(p)
      valores_q.append(q)

# K_distance

dict = {'dist': kd_values, 'p': valores_p, 'q': valores_q}
dists = pd.DataFrame(dict)
nearest=dists.groupby('p')['dist'].min()
k_distance=statistics.mean(nearest)


# Guardado de datos.

archivo="Resumen.txt"
with open (archivo, "w") as arch:
    #arch.write(f"Tiempo de ejecución {round(elapsed_time,2)} segundos\n")
    arch.write(f"ONVG: {ONVG}\n")
    arch.write(f"k-distancia: {round(k_distance,2)}\n")
    arch.write(f"Hipervolumen: {round(HVOL,2)}\n")
    arch.write("Opción - Riesgo Minimizado - Distancia - Refugios\n")
    for n in range(len(FO3_values)):
        arch.write(f"    {n}           {FO3_values[n]}          {round(FO1_values[n],2)}km    {FO2_values[n]}\n")
    arch.write("\nCombinaciones de épsilon infactibles:\n")
    for ec1, ec2 in zip(infactible_ec1, infactible_ec2):
        arch.write(f"ec1: {round(ec1,2)}, ec2: {round(ec2,2)}\n")
n_max = len(FO1_values)
it=np.linspace(0,n_max-1,n_max)
for n in it:
    n = int(n)
    FO1_n = FO1_values[n]
    FO2_n = FO2_values[n]
    FO3_n = FO3_values[n]
    Ev_n= Ev_values[n]
    R_n=R_values[n]
    ec1_n=ec1_values[n]
    ec2_n=ec2_values[n]
    Ev_Ref_n=Ev_Ref_values[n]
    dis_ref_n=dis_ref_values[n]
    D_prom_n=D_prom_values[n]
    Ev_Ref_n=Ev_Ref_values[n]
    dis_ref_n=dis_ref_values[n]
    D_prom_n=D_prom_values[n]
    archivo_respuesta=f"opcion_{n}.txt"
    with open (archivo_respuesta, "w") as arch_r:
        arch_r.write(f"La combinación de épsilon es ec1={round(ec1_n,2)} y ec2={round(ec2_n,2)}.\n\n")
        arch_r.write(f"La distancia recorrida es de {round(FO1_n,2)} km.\n")
        arch_r.write(f"Se deben abrir {FO2_n} refugios.\n")
        arch_r.write(f"El riesgo minimizado es de {FO3_n}.\n")
        arch_r.write(f"El total de personas asignadas es {Ev_n}.\n\n")
        arch_r.write("La configuración de la solución es:")
        for i in refugios:
            i = str(i)
            x_val = R_n[str(i)]['x']  # Obtener el valor de x para el refugio i
            Ev_val =Ev_Ref_n[i]['evacuados']
            dis_val=dis_ref_n[i]['distanciatotal']
            D_val=D_prom_n[i]['distanciamedia']
            if x_val > 0:
               arch_r.write(f"\nPara el refugio {i}:\n")
               arch_r.write(f" + Se refugian {Ev_val} personas\n")
               arch_r.write(f" + Recorren en total {round(dis_val,2)} km\n")
               arch_r.write(f" + Cada una recorre en promedio {round(D_val,2)} km\n")
               for j in zonas_demanda:
                   j=str(j)
                   y_val = R_n[i]['y'][j]  # Obtener el valor de y[i,j] para el refugio i y la zona de demanda j
                   if y_val >0:
                       arch_r.write(f"Asignar {round(y_val,0)} personas de la zona de demanda {j}\n")
            else:
                arch_r.write(f"\nEl refugio {i} no se debe abrir.\n")