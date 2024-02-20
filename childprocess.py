import subprocess
import shlex


from utilites.ipc import IPC, IPC_Pipes, IPC_Network


class Childprocess:
    class IPC_Pipes(IPC_Pipes):
        ...

    class IPC_Network(IPC_Network):
        ...

    InterProcessCommunication: IPC

    __alive: bool
    __death_confirm: bool

    def __init__(self, ipc_instance: IPC):
        self.__death_confirm = False
        self.InterProcessCommunication = ipc_instance
        self.__alive = True
        self.run()

    def run(self):
        while self.is_running:
            self.cycle()
        self.__death_confirm = True

    def cycle(self):
        ...

    def __del__(self):
        self.__alive = False
        while not self.__death_confirm:
            pass
        del self.InterProcessCommunication

    @property
    def is_running(self):
        return self.__alive

    @classmethod
    def spawn(cls, file: str, **kwargs) -> None:
        """
        Used to spawn a new child process
        :param file: location of subprocess script
        """

        cmd = f'python "{file}" ' + ' '.join([f'--{key} {kwargs[key]}' for key in kwargs.keys()])
        cmds = shlex.split(cmd)
        subprocess.Popen(cmds, start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
