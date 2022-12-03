import socket
from time import sleep


def main():
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    allips = [ip[-1][0] for ip in interfaces]

    msg = b'hello world'
    while True:
        for ip in allips:
            print(f'sending on localhost')
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((ip, 12345))
            sock.sendto(msg, ("255.255.255.255", 12345))
            b = sock.recvfrom(128)
            print(b)
            sock.close()

        sleep(2)


main()
