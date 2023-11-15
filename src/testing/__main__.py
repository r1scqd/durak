import unittest

from ..logic.durak import Durak, ACE
from ..logic.serialization import DurakSerialized


class TestGame(unittest.TestCase):
    def test_1(self, ):
        d = Durak()
        assert d.attacker_index == 0
        assert len(d.deck) == 36 - 2 * 6
        assert d.attacking_player.n_cards == d.defending_player.n_cards == 6

        d.attack(d.attacking_player[0])
        d.finish_turn()

        assert d.attacker_index == 0
        assert d.defending_player.n_cards == 7
        assert d.attacking_player.n_cards == 6
        assert len(d.deck) == 36 - 13

    def test_trump_not_ace(self):
        for _ in range(10000):
            d = Durak()
            assert d.trump[0] != ACE
            assert d.trump == d.deck[-1]


class TestSerialization(unittest.TestCase):
    def test_ser1(self):
        g = DurakSerialized()

        g.attack(g.players[0].cards[0])

        jg = g.serialized()
        g2 = DurakSerialized(jg)

        assert g.attacker_index == g2.attacker_index
        assert g.winner == g2.winner
        assert g.field == g2.field

        assert all(c1 == c2 for c1, c2 in zip(g.deck, g2.deck))

        for p1, p2 in zip(g.players, g2.players):
            assert p1.index == p2.index
            assert p1.cards == p2.cards


if __name__ == '__main__':
    unittest.main()
