import time
import json
#!pip install gurobipy
import gurobipy as gp  # import the installed package
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from gurobipy import *
from gurobipy import GRB

# Tiempo de inicio d ejecución.
st=time.time()


## Leer Archivos y Definir Modelo
#Definir parámetros
File=pd.ExcelFile("Scenarios/government.xlsx")
d=File.parse('distancias')
d=d.values
e=File.parse('evacuados')
e=e.values
c=File.parse('capacidad')
c=c.values
p=File.parse('riesgo')
p=p.values
w=0.5

#Crear modelo
model=Model("Modelo 1")

#tamaño del conjunto i
refugios=range(c.shape[1])
#tamaño del conjunto j
zonas_demanda=range(e.shape[1])

#Establecer variables
x= model.addVars(refugios,vtype=GRB.BINARY, name='x') #refugio i abierto o no
y= model.addVars(refugios,zonas_demanda,lb=0, vtype=GRB.INTEGER, name='y') #número de personas de la zona de demanda j asignados al refugio i
s=model.addVar(lb=0.0, ub=4, vtype=GRB.CONTINUOUS, name='s') #máximo riesgo asociado a la apertura de un refugio

#Establecer restricciones
model.addConstrs(s>=p[0,i]*x[i] for i in refugios) #R1/Linealización de FO 3
model.addConstrs(y.sum("*",j)==e[0,j] for j in zonas_demanda) #R2/Asignar a todos los evacuados
model.addConstrs(y.sum(i,"*")<=c[0,i] for i in refugios) #R3/No superar la capacidad
model.addConstrs(x[i]>=(y.sum(i,"*"))/c[0,i] for i in refugios) #R4.1 Asignar a personas solo a refugios abiertos
model.addConstrs(x[i]<=(1-w)+w*(y.sum(i,"*")) for i in refugios) #R4.2 Asignar a personas solo a refugios abiertos

## Minimizar FO1

#Establecer Función Objetivo
FO1=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda)
FO2=gp.quicksum(x[i] for i in refugios)
FO3=s
model.setObjective(FO1, sense=GRB.MINIMIZE)

#Optimizar Modelo
model.optimize()
#Para mayor detalle, eliminar # de las tres siguientes lineas
#for v in model.getVars():
#  print(f"{v.VarName} {v.X:g}")
#print(f"Obj: {model.ObjVal:g}")

FO1_A=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda).getValue()
FO2_A=sum(x[i].x for i in refugios)
FO3_A=max(p[0, i] for i in refugios if x[i].x > 0)
Ev_A = sum(y[i,j].x for i in refugios for j in zonas_demanda)


## Minimizar FO2
model.setObjective(FO2, sense=GRB.MINIMIZE)

#Optimizar Modelo
model.optimize()
#Para mayor detalle, eliminar # de las tres siguientes lineas
#for v in model.getVars():
#  print(f"{v.VarName} {v.X:g}")
#print(f"Obj: {model.ObjVal:g}")

FO1_B=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda).getValue()
FO2_B=sum(x[i].x for i in refugios)
FO3_B=max(p[0, i] for i in refugios if x[i].x > 0)
Ev_B = sum(y[i,j].x for i in refugios for j in zonas_demanda)

## Minimizar FO3

#Establecer Función Objetivo
model.setObjective(FO3, sense=GRB.MINIMIZE)

#Optimizar Modelo
model.optimize()
#Para mayor detalle, eliminar # de las tres siguientes lineas
#for v in model.getVars():
#  print(f"{v.VarName} {v.X:g}")
#print(f"Obj: {model.ObjVal:g}")

FO1_C=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda).getValue()
FO2_C=sum(x[i].x for i in refugios)
FO3_C=max(p[0, i] for i in refugios if x[i].x > 0)
Ev_C = sum(y[i,j].x for i in refugios for j in zonas_demanda)

## Modelo con Épsilon Constraint

# Establecer límite inferior y límite superior de las restricciones de epsílon
ec1_lb=min(FO1_A,FO1_B,FO1_C)
ec1_ub=max(FO1_A,FO1_B,FO1_C)
ec2_lb=min(FO2_A,FO2_B,FO2_C)
ec2_ub=max(FO2_A,FO2_B,FO2_C)

# Establecer cantidad de elementos en el arreglo correspondiente a ec1
# Para mayor cantidad de iteraciones modificar el número entero en la línea 1 y 2
if ec1_ub-ec1_lb > 10:
  elementos_ec1= 10
else:
  elementos_ec1 = ec1_ub-ec1_lb
  
ec1=np.linspace(ec1_lb,ec1_ub,elementos_ec1)


# Establecer cantidad de elementos en el arreglo correspondiente a ec2
# Para mayor cantidad de iteraciones modificar el número entero en la línea 1 y 2
if ec2_ub-ec2_lb > 10:
  elementos_ec2= 10
else:
  elementos_ec2 = int(ec2_ub-ec2_lb+1)
  
ec2=np.linspace(ec2_lb,ec2_ub,elementos_ec2)


# Crear modelo con restricciones épsilon y optimizar
FO1_values = []
FO2_values = []
FO3_values = []
Ev_values = []
R_values=[]
ec1_values=[]
ec2_values=[]
infactible_ec1 = []
infactible_ec2 = []
debiles_ec1 = []
debiles_ec2 = []
dis_ref_values=[]
Ev_Ref_values=[]
D_prom_values=[]
guardar = {}

for k in ec1:
  for l in ec2:
    #Crear modelo
    model_ec=Model("Modelo 2")
    #tamaño del conjunto i
    refugios=range(c.shape[1])
    #tamaño del conjunto j
    zonas_demanda=range(e.shape[1])
    #Establecer variables
    x= model_ec.addVars(refugios,vtype=GRB.BINARY, name='x') #refugio i abierto o no
    y= model_ec.addVars(refugios,zonas_demanda,lb=0, vtype=GRB.INTEGER, name='y') #número de personas de la zona de demanda j asignados al refugio i
    s= model_ec.addVar(lb=0.0, ub=4, vtype=GRB.CONTINUOUS, name='s') #máximo riesgo asociado a la apertura de un refugio #agregar restriccion menor que 1
    #Establecer Función Objetivo
    FO1=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda)
    FO2=gp.quicksum(x[i] for i in refugios)
    FO3=s
    model_ec.setObjective(FO3, sense=GRB.MINIMIZE)
    #Establecer restricciones
    model_ec.addConstrs(s>=p[0,i]*x[i] for i in refugios) #R1/Linealización de FO 3
    model_ec.addConstrs(y.sum("*",j)==e[0,j] for j in zonas_demanda) #R2/Asignar a todos los evacuados
    model_ec.addConstrs(y.sum(i,"*")<=c[0,i] for i in refugios) #R3/No superar la capacidad
    model_ec.addConstrs(x[i]>=(y.sum(i,"*"))/c[0,i] for i in refugios) #R4.1 Asignar a personas solo a refugios abiertos
    model_ec.addConstrs(x[i]<=(1-w)+w*(y.sum(i,"*")) for i in refugios) #R4.2 Asignar a personas solo a refugios abiertos
    #Restricciones de Epsilon Constraint
    model_ec.addConstr(quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda)<=k)
    model_ec.addConstr(quicksum(x[i] for i in refugios)<=l)
    #Optimizar Modelo
    print(f"ec1:{round(k,2)}, ec2:{round(l,2)}")
    model_ec.optimize()
    if model_ec.status == gp.GRB.INFEASIBLE:
      infactible_ec1.append(k)
      infactible_ec2.append(l)
      print("El modelo es infactible.")
      print("----------------------------------------------------------------------------------------------------------------------")
    else:
        #for v in model_ec.getVars():
            #print(f"{v.VarName} {v.X:g}")
        #print(f"Obj: {model_ec.ObjVal:g}")
        FO1_ec=gp.quicksum(d[i,j]*y[i,j] for i in refugios for j in zonas_demanda).getValue()#sumar distancia total con valores optimos
        FO2_ec=sum(x[i].x for i in refugios)#sumar valores de x
        FO3_ec=model_ec.getObjective().getValue()
        Ev_ec=sum(y[i,j].x for i in refugios for j in zonas_demanda)
        R_ec=model_ec.getVars()
        R_ec_values = [var.x for var in R_ec]
        combinacion=(FO1_ec, FO2_ec, FO3_ec)
        # Verificar si la combinación actual es débilmente dominada
        dominada_debil = False
        for key, value in guardar.items():
            if (value['FO1'] <= FO1_ec and value['FO2'] <= FO2_ec and value['FO3'] == FO3_ec):
                dominada_debil = True
                debiles_ec1.append(k)
                debiles_ec2.append(l)
                break
        if not dominada_debil:
            guardar[combinacion] = {'FO1': FO1_ec, 'FO2': FO2_ec, 'FO3': FO3_ec}
            FO1_values.append(FO1_ec)
            FO2_values.append(FO2_ec)
            FO3_values.append(FO3_ec)
            Ev_values.append(Ev_ec)
            R_ec_values = {}  # Diccionario para almacenar los valores de las variables
            Ev_r={}
            dis_ref={}
            D_prom={}
            for i in refugios:
                R_ec_values[i] = {'x': x[i].x, 'y': {j: y[i,j].x for j in zonas_demanda}}
                a=sum(y[i,j].x for j in zonas_demanda)
                Ev_r[i]={'evacuados':a}#cantidad de refugiados en i
                b=sum(d[i,j]*y[i,j] for j in zonas_demanda).getValue()
                dis_ref[i]={'distanciatotal':b}
                if a!=0:
                  m=b/a
                  D_prom[i]={'distanciamedia':m}
                else:
                  D_prom[i]={'distanciamedia': 0}
            D_prom_values.append(D_prom)
            dis_ref_values.append(dis_ref)
            Ev_Ref_values.append(Ev_r)
            R_values.append(R_ec_values)
            ec1_values.append(k)
            ec2_values.append(l)
        #print(f"La distancia recorrida es de: {FO1_ec}")
        #print(f"Se deben abrir {FO2_ec} refugios")
        #print(f"El riesgo minimizado es de {FO3_ec}")
        #print(f"El total de personas asignadas es {Ev_ec}")
        #print(f"La configuración de la solución es {R_ec}")
        print("----------------------------------------------------------------------------------------------------------------------")
        
### Representación gráfica de los resultados de la optimización
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(FO1_values, FO2_values, FO3_values)
ax.set_xlabel('FO1')
ax.set_ylabel('FO2')
ax.set_zlabel('FO3')
plt.title("Resultados de la optimización")
plt.savefig("Figura 3D")
#plt.show()

from pandas.plotting import scatter_matrix
A=np.vstack((FO1_values,FO2_values,FO3_values)).T
AA=pd.DataFrame(A, columns =['FO1', 'FO2', 'FO3'])
scatter_matrix(AA, figsize = (6, 6), diagonal = 'hist')
plt.savefig("Matriz Grafica de dispersion")
#plt.show()

et=time.time()
elapsed_time=et-st
archivo="Resumen.txt"
with open (archivo, "w") as arch:
    arch.write(f"Tiempo de ejecución {round(elapsed_time,2)} segundos\n")
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
            x_val = R_n[i]['x']  # Obtener el valor de x para el refugio i
            Ev_val =Ev_Ref_n[i]['evacuados']
            dis_val=dis_ref_n[i]['distanciatotal']
            D_val=D_prom_n[i]['distanciamedia']
            if x_val > 0:
               arch_r.write(f"\nPara el refugio {i}:\n")
               arch_r.write(f" + Se refugian {Ev_val} personas\n")
               arch_r.write(f" + Recorren en total {round(dis_val,2)} km\n")
               arch_r.write(f" + Cada una recorre en promedio {round(D_val,2)} km\n")
               for j in zonas_demanda:
                   y_val = R_n[i]['y'][j]  # Obtener el valor de y[i,j] para el refugio i y la zona de demanda j
                   if y_val >0:
                       arch_r.write(f"Asignar {round(y_val,0)} personas de la zona de demanda {j}\n")
            else:
                arch_r.write(f"\nEl refugio {i} no se debe abrir.\n")