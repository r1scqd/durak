from threading import Timer

from .durak import TurnFinishResult
from .serialization import DurakSerialized
from ..network.network import Networking


class DurakNetGame:
    def __init__(self, my_id, remote_id, remote_addr, ports):
        self.state = DurakSerialized()

        self._my_id = int(my_id)
        self._remote_id = int(remote_id)
        self._remote_addr = remote_addr

        assert self._my_id != 0 and self._remote_id != 0 and self._my_id != self._remote_id

        me_first = self._my_id < self._remote_id

        self._my_index = 0 if me_first else 1
        self._opp_index = 1 if me_first else 0

        network1 = Networking(port_no=ports[0])
        network2 = Networking(port_no=ports[1])

        self._receiver = network1 if me_first else network2
        self._receiver.bind("")

        self._sender = network2 if me_first else network1

        self.on_state_updated = lambda _: ...
        self.on_opponent_quit = lambda: ...

    def _send_game_state(self):
        self.on_state_updated(self.state)
        self._sender.send_json({
            'action': 'state',
            'state': self.state.serialized()
        }, self._remote_addr)

    def _send_quit(self):
        self._sender.send_json({
            'action': 'quit'
        }, self._remote_addr)

    def finish_turn(self) -> TurnFinishResult:
        g = self.state
        if g.field:
            if self.is_my_turn and g.any_unbeaten_cards:
                return TurnFinishResult.CANT_FORCE_TO_TAKE
            elif not self.is_my_turn and not g.any_unbeaten_cards:
                return TurnFinishResult.CANT_TAKE_NOW
            else:
                result = g.finish_turn()
                self._send_game_state()
                return result
        else:
            return TurnFinishResult.EMPTY

    def attack(self, card):
        assert self.is_my_turn
        result = self.state.attack(card)
        if result:
            self._send_game_state()
        return result

    def defend(self, my_card, field_card):
        assert not self.is_my_turn
        g = self.state
        if g.field:

            if isinstance(field_card, int):
                field_card = list(g.field.keys())[field_card]

            assert my_card in self.state.defending_player.cards
            assert field_card in self.state.field.keys()
            result = g.defend(field_card, my_card)
            if result:
                self._send_game_state()
            return result
        else:
            return False

    def _new_game(self):

        self.state = DurakSerialized()

        Timer(0.5, self._send_game_state).start()

    def _on_remote_message(self, data):
        action = data['action']
        if action == 'state':
            self.state = DurakSerialized(data['state'])
            self.on_state_updated(self.state)
        elif action == 'quit':
            self.on_opponent_quit()

    def start(self):

        self._receiver.run_reader_thread(self._on_remote_message)

        if self._my_index == 0:
            self._new_game()

    def stop(self):
        self._send_quit()
        self._receiver.read_running = False

    @property
    def my_cards(self):
        return self.state.players[self._my_index].cards

    @property
    def opp_cards(self):
        return self.state.players[self._opp_index].cards

    @property
    def is_my_turn(self):
        return self.state.attacker_index == self._my_index

    def is_me(self, index):
        return index == self._my_index

    ME = 'me'
    OPPONENT = 'opponent'

    @property
    def winner(self):
        if self.state.winner is not None:
            return self.ME if self._my_index == self.state.winner else self.OPPONENT

    @property
    def my_index(self):
        return self._my_index
