import unittest
from profiles import check_risk_management

class TestRiskManagement(unittest.TestCase):
    def test_max_position_size(self):
        profile = {'max_position_size': 1.0}
        order = {'size': 1.5}
        ok, msg = check_risk_management(profile, order)
        self.assertFalse(ok)
        self.assertIn('размера позиции', msg)

    def test_max_trades_per_day(self):
        profile = {'max_trades_per_day': 2}
        order = {'size': 0.5}
        stats = {'trades_today': 2}
        ok, msg = check_risk_management(profile, order, stats)
        self.assertFalse(ok)
        self.assertIn('лимит сделок', msg)

    def test_max_daily_loss(self):
        profile = {'max_daily_loss': 100}
        order = {'size': 0.5}
        stats = {'daily_loss': -120}
        ok, msg = check_risk_management(profile, order, stats)
        self.assertFalse(ok)
        self.assertIn('дневного убытка', msg)

    def test_ok(self):
        profile = {'max_position_size': 2.0, 'max_trades_per_day': 5, 'max_daily_loss': 100}
        order = {'size': 1.0}
        stats = {'trades_today': 1, 'daily_loss': -10}
        ok, msg = check_risk_management(profile, order, stats)
        self.assertTrue(ok)
        self.assertEqual(msg, 'Ок')

if __name__ == '__main__':
    unittest.main() 