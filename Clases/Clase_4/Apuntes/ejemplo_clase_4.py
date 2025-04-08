import tempfile, os

def main():
    file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    file_name = file.name
    file.close()

    create_children(file_name, "Soy el hijo 1")
    create_children(file_name, "Soy el hijo 2")

def create_children(file_name, message):
    pid = os.fork()
    if pid == 0:
        print(f'{message}, mi PID es {os.getpid()}, el ID de mi padre es {os.getppid()}')

        with open(file_name, 'a') as f:
            f.write(f'{message}, leyendo el archivo, mi PID es {os.getpid()}, el id de mi padre es {os.getppid()}\n')

        os._exit(0)  

    os.wait()  
    with open(file_name, 'r') as f:
        contenido = f.read()
        print(f"Contenido leido: {contenido}")

if __name__ == '__main__':
    main()
