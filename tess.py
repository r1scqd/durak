import json
import logging
import socket
import threading
import time

from loguru import logger


class Networking:
    BUFF = 4096
    TIMEOUT = 2.0

    @classmethod
    def get_socket(cls, broadcast=False, timeout=TIMEOUT):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except AttributeError:

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if broadcast:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        return sock

    def recv_json(self):
        try:

            data, addr = self._socket.recvfrom(self.BUFF)

            return json.loads(data.decode('utf-8', errors='ignore')), addr
        except json.JSONDecodeError:
            logging.error(f'JSONDecodeError!')
        except socket.timeout:
            pass
        except KeyboardInterrupt:
            raise
        return None, None

    def recv_json_until(self, predicate, timeout):
        t0 = time.monotonic()
        while time.monotonic() < t0 + timeout:
            data, addr = self.recv_json()
            if predicate(data):
                return data, addr
        return None, None

    def run_reader_thread(self, callback):
        self.read_running = True

        def reader_job():
            while self.read_running:
                data, _ = self.recv_json()
                if data:
                    callback(data)

        thread = threading.Thread(target=reader_job, daemon=True)
        thread.start()
        return thread

    def bind(self, to=""):
        self._socket.bind((to, self.port_no))

    def __init__(self, port_no, broadcast=False):
        self.read_running = False
        self.port_no = port_no
        self._socket = self.get_socket(broadcast=broadcast)

    def send_json(self, j, to):
        data = bytes(json.dumps(j), 'utf-8')
        return self._socket.sendto(data, (to, self.port_no))

    def send_json_broadcast(self, j):
        return self.send_json(j, socket.gethostbyname('<broadcast>'))
        # return self.send_json(j, "192.168.1.255")

    def __del__(self):
        logging.info('Closing socket')
        self._socket.close()


import random
import logging
import threading


class DiscoveryProtocol:
    A_DISCOVERY = 'discovery'
    A_STOP_SCAN = 'stop_scan'

    def __init__(self, pid, port_no):
        assert pid
        self._my_pid = pid
        self._network = Networking(port_no, broadcast=True)
        self._network.bind()

    def _send_action(self, action, data=None):
        data = data or {}
        self._network.send_json_broadcast({'action': action, 'sender': self._my_pid, **data})

    def _is_message_for_me(self, d):
        return d and d.get('action') in [self.A_DISCOVERY, self.A_STOP_SCAN] and d.get('sender') != self._my_pid

    def run(self):
        while True:
            logging.info('Scanning...')
            self._send_action(self.A_DISCOVERY)

            data, addr = self._network.recv_json_until(self._is_message_for_me, timeout=5.0)

            if data:
                action, sender = data['action'], data['sender']
                if action == self.A_DISCOVERY:
                    self._send_action(self.A_STOP_SCAN, {'to_pid': sender})
                elif action == self.A_STOP_SCAN:
                    if data['to_pid'] != self._my_pid:
                        continue
                return addr, sender

    def run_in_background(self, callback: callable):
        def await_with_callback():
            results = self.run()
            callback(*results)

        threading.Thread(target=await_with_callback, daemon=True).start()


if __name__ == '__main__':
    print('Testing the discovery protocol.')
    pid = random.getrandbits(64)
    print('pid =', pid)
    info = DiscoveryProtocol(pid, 5005).run()
    print("success: ", info)
