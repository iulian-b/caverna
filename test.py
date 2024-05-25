import platform

print(platform.system())

if platform.system() == "Windows":
    print("W")
else:
    print("L")