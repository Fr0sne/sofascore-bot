import os

with open("libs.txt", "r") as f:
     for line in f.readlines():
          lib = line.split()[0]
          print(f"Instalando {lib}")
          print(f"pip {lib}")
          os.system(f"pip install {lib}")
