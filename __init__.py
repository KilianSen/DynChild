import subprocess
import socket
import argparse
import sys
import shlex
import time

from utilities.ipc import IPC, IPC_Pipes

import sys
import logging

logging.basicConfig(filename='log.log', level='INFO')
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


sys.excepthook = handle_exception


parameter_identifier = 'seperate_process'


def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))  # Bind to a free port provided by the host.
        return s.getsockname()[1]


def local(func):
    def wrap(*args, **kwargs):
        return func(*args, **kwargs)

    return wrap


def ipc_send():
    ...


def handle_remote_function_execute(self, attr, args, kwargs):
    logger.info(f'EXECUTE REMOTE {attr}{*args, *kwargs}')
    object.__getattribute__(self, '__internal_ipc').send(f'EXEC {attr} {args} {kwargs}')


def handle_remote_var_get(self, attr):
    logger.info(f'REQUEST REMOTE {attr}')
    object.__getattribute__(self, '__internal_ipc').send(f'GET {attr}')


def handle_remote_var_set(self, attr, val):
    logger.info(f'SET REMOTE {attr} to {val}')
    object.__getattribute__(self, '__internal_ipc').send(f'SET {attr} {val}')


def handle_local_function_execute(self, attr, args, kwargs):
    return attr(*args, **kwargs)


def handle_local_var_get(self, attr):
    return object.__getattribute__(self, attr)


def handle_local_var_set(self, attr, val):
    return object.__setattr__(self, attr, val)


def handle_local_init(self, port_pair):
    return object.__setattr__(self, '__internal_ipc', IPC_Pipes(port_pair[1], port_pair[0]))


def handle_remote_init(self):
    ip_pair = find_free_port(), find_free_port()
    object.__setattr__(self, '__internal_ipc', IPC_Pipes(ip_pair[0], ip_pair[1]))

    return ip_pair


class ChildMeta(type):
    def __call__(cls, *args, **kwargs):
        instance = cls.__new__(cls, *args, **kwargs)
        object.__setattr__(instance, parameter_identifier, False)
        if parameter_identifier in kwargs:
            object.__setattr__(instance, parameter_identifier, kwargs[parameter_identifier])

        if 'port_pair' in kwargs:
            object.__setattr__(instance, 'port_pair', kwargs['port_pair'])

        if not(parameter_identifier in kwargs and parameter_identifier):
            port_pair = object.__getattribute__(instance, 'port_pair')
            handle_local_init(port_pair=port_pair)
        else:
            port_pair = handle_remote_init(instance)
            instance._spawn(port_pair=port_pair, args=args, kwargs=kwargs)
            time.sleep(1)

        if 'port_pair' in kwargs:
            del kwargs['port_pair']

        if parameter_identifier in kwargs:
            del kwargs[parameter_identifier]

        instance.__init__(*args, **kwargs)
        return instance


class Child(metaclass=ChildMeta):
    file: str = None

    # __ipc: IPC = IPC_Pipes()

    def __init__(self):
        logger.info('INIT')
        ...

    def __child_internal_init__(self):
        pass

    def __getattribute__(self, name):
        @local
        def test():
            ...

        attr = object.__getattribute__(self, name)
        if hasattr(attr, '__call__'):
            if attr.__name__ == test.__name__:
                return attr

            def newfunc(*args, **kwargs):
                if object.__getattribute__(self, parameter_identifier):
                    return handle_local_function_execute(self, attr, args, kwargs)
                else:
                    return handle_remote_function_execute(self, attr, args, kwargs)

            return newfunc
        else:
            if object.__getattribute__(self, parameter_identifier):
                return handle_local_var_get(self, name)
            return handle_remote_var_get(self, name)

    def __setattr__(self, key, value):
        if object.__getattribute__(self, parameter_identifier):
            return handle_local_var_set(self, key, value)
        return handle_remote_var_set(self, key, value)

    @local
    def _spawn(self, **kwargs) -> None:
        """
        Used to spawn a new child process
        :param file: location of subprocess script
        """
        cmd = f'python "{object.__getattribute__(self, "file")}" ' + \
              ' '.join([f'--{key} {kwargs[key]}' for key in kwargs.keys()])
        logger.info(cmd)
        cmds = shlex.split(cmd)
        subprocess.Popen(cmds, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        time.sleep(1)
        logger.info(123)


class SomeClass(Child):
    file = __file__

    def function_1(self, p1, player2):
        logger.info('HELLO', self.seperate_process)


def spawner_entry(cls):
    if __name__ == '__main__':
        try:
            ports = sys.argv[1:4]
            p1 = ports[1][1:len(ports[1]) - 1]
            p2 = ports[2][:len(ports[2]) - 1]
            logging.warning('IPCO')
            cls(seperate_process=True, port_pair=(p1, p2))
        except IndexError as _:
            ...


spawner_entry(SomeClass)

if __name__ == '__main__':
    s = SomeClass(seperate_process=False)
    s.function_1(2, player2=12)
    s.file = "LOL"
    logger.info(s.file)
    while True:
        ...
