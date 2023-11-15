import random
import logging
import threading

from src.network import network


class DiscoveryProtocol:
    A_DISCOVERY = 'discovery'
    A_STOP_SCAN = 'stop_scan'

    def __init__(self, pid, port_no):
        assert pid
        self._my_pid = pid
        self._network = network.Networking(port_no, broadcast=True)
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
    print(pid)
    print('pid =', pid)
    info = DiscoveryProtocol(pid, 37020).run()
    print("success: ", info)
