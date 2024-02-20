import socket
import struct
from multiprocessing.connection import Connection, answer_challenge, deliver_challenge
from multiprocessing.connection import Listener, Client
from queue import Queue
from threading import Thread


class CommunicationType:
    class Blank:
        class Address:
            ip: str
            port: int

            def __init__(self, ip: str, port: int):
                self.ip = ip
                self.port = port

        local: Address
        target: Address

        def __init__(self, local: Address, target: Address):
            self.local = local
            self.target = target

    class Pipes(Blank):
        def __init__(self, local_port: int, target_port: int):
            super().__init__(CommunicationType.Blank.Address('localhost', local_port),
                             CommunicationType.Blank.Address('localhost', target_port))

    class Network(Blank):
        def __init__(self, local_port: int, target_ip: str, target_port: int):
            super().__init__(CommunicationType.Blank.Address('localhost', local_port),
                             CommunicationType.Blank.Address(target_ip, target_port))


class IPCClient:
    def __init__(self, target_port: int, target_ip: str = 'localhost'):
        self.target_port = target_port
        self.target_ip = target_ip

    def send(self, data: object):
        try:
            ipc = Client((self.target_ip, self.target_port))
            ipc.send(data)
            ipc.close()
            return True, None
        except Exception as ex:
            return False, ex


class IPCListener:
    def __init__(self, port: int, ip: str = 'localhost'):
        self.__queue = Queue()
        self.__alive = True
        self.__listener = Listener((ip, port))
        self.__thread = Thread(target=self.cycle, daemon=True, name=f'IPC Listner {port}')
        self.__thread.start()

    def stop(self):
        self.__alive = False

    def __del__(self):
        self.stop()

    def cycle(self):
        connection = self.__listener.accept()
        while self.__alive:
            self.__queue.put(connection.recv())

    @property
    def available(self):
        return not self.__queue.empty()

    @property
    def get(self):
        if self.available:
            return self.__queue.get()
        return None


class IPC:
    __i_client: IPCClient
    __i_listener: IPCListener

    def __init__(self, com_type: CommunicationType.Blank):
        self.__i_client = IPCClient(com_type.target.port, com_type.target.ip)
        self.__i_listener = IPCListener(com_type.local.port, com_type.local.ip)

    def send(self, data: object):
        self.__i_client.send(data)

    @property
    def available(self) -> bool:
        return self.__i_listener.available

    def get(self) -> object:
        return self.__i_listener.get


class IPC_Pipes(IPC):
    def __init__(self, local_port: int, target_port: int):
        super().__init__(CommunicationType.Pipes(local_port, target_port))


class IPC_Network(IPC):
    def __init__(self, local_port: int, target_port: int, target_ip: str):
        super().__init__(CommunicationType.Network(local_port, target_port, target_ip))
