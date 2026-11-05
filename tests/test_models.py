import math
import unittest
from dataclasses import replace
from valuation_lab import DCFInputs, NAVItem, dcf, comps, adjusted_nav, wacc
from valuation_lab.example import ASSETS, LIABILITIES, PEERS, run_examples


class DCFTests(unittest.TestCase):
    def setUp(self):self.base=DCFInputs()
    def test_known_baseline(self):
        r=dcf(self.base)
        self.assertAlmostEqual(r['ev'],86.44468226943198,places=9)
        self.assertAlmostEqual(r['equity'],66.44468226943198,places=9)
    def test_first_year_working_capital_increment(self):
        r=dcf(self.base)['rows'][0]
        self.assertAlmostEqual(r['revenue'],108)
        self.assertAlmostEqual(r['delta_nwc'],1.6)
        self.assertAlmostEqual(r['fcff'],7.04)
    def test_terminal_cash_flow_is_rederived(self):
        r=dcf(self.base)
        self.assertAlmostEqual(r['terminal_fcff'],9.99197192448,places=10)
        self.assertFalse(math.isclose(r['terminal_fcff'],r['rows'][-1]['fcff']*1.02))
    def test_independent_present_value_calculation(self):
        # Independently fixed analytical FCFF and year-six values.
        flows=(7.04,7.8624,8.47152,9.0393408,9.550929024)
        ev=sum(cf/1.12**t for t,cf in enumerate(flows,1))+9.99197192448/.10/1.12**5
        self.assertAlmostEqual(dcf(self.base)['equity'],ev-20,places=9)
    def test_higher_wacc_reduces_value(self):
        self.assertLess(dcf(replace(self.base,discount_rate=.13))['equity'],dcf(self.base)['equity'])
    def test_additional_obligation_once(self):
        r=dcf(replace(self.base,additional_obligation=4))
        self.assertAlmostEqual(r['equity'],62.44468226943198)
        self.assertAlmostEqual(r['equity_before_obligation']-r['equity'],4)
    def test_unit_scaling(self):
        scaled=replace(self.base,revenue0=1000,nwc0=200,net_debt=200)
        self.assertAlmostEqual(dcf(scaled)['equity'],dcf(self.base)['equity']*10)
    def test_net_cash(self):
        self.assertAlmostEqual(dcf(replace(self.base,net_debt=-5))['equity'],dcf(self.base)['ev']+5)
    def test_invalid_inputs(self):
        for field,value in [('discount_rate',.02),('discount_rate',float('nan')),
                            ('revenue0',0),('tax_rate',1.1),('capex_ratio',-1),
                            ('additional_obligation',-1),('terminal_growth',-1),
                            ('growth_rates',()),('growth_rates',(-1,)),('revenue0',True)]:
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):
                dcf(replace(self.base,**{field:value}))
    def test_terminal_margin_override(self):
        a=replace(self.base,ebit_margin=.14,terminal_ebit_margin=.12)
        self.assertAlmostEqual(dcf(a)['terminal_fcff'],dcf(self.base)['terminal_fcff'])
    def test_wacc_weights(self):self.assertAlmostEqual(wacc(.16,.08,.25,.6,.4),.12)
    def test_wacc_rejects_bad_weights(self):
        with self.assertRaises(ValueError):wacc(.16,.08,.25,.6,.5)


class CompsTests(unittest.TestCase):
    def test_reference_results(self):
        r=comps(PEERS,16,7.5,20)
        self.assertEqual(r['median_ev_ebitda'],6)
        self.assertEqual(r['median_per'],10)
        self.assertEqual(r['equity_ev_ebitda'],76)
        self.assertEqual(r['equity_per'],75)
    def test_per_not_affected_by_net_debt(self):
        self.assertEqual(comps(PEERS,16,7.5,100)['equity_per'],75)
    def test_missing_and_negative_denominators(self):
        for peers in [(),(replace(PEERS[0],ebitda=0),),(replace(PEERS[0],net_income=-1),)]:
            with self.assertRaises(ValueError):comps(peers,16,7.5,20)
    def test_duplicate_peers_rejected(self):
        with self.assertRaises(ValueError):comps((PEERS[0],PEERS[0]),16,7.5,20)
    def test_fdd_reference(self):
        self.assertEqual(comps(PEERS,16.5,7.5,20,4)['equity_ev_ebitda'],75)


class NAVTests(unittest.TestCase):
    def test_book_to_adjusted_reconciliation(self):
        r=adjusted_nav(ASSETS,LIABILITIES)
        self.assertEqual((r['book_assets'],r['book_liabilities'],r['book_equity']),(115,50,65))
        self.assertEqual((r['adjusted_assets'],r['adjusted_liabilities'],r['equity']),(126,56,70))
        self.assertEqual(r['book_equity']+r['equity_adjustment'],r['equity'])
    def test_nav_is_already_equity(self):
        r=adjusted_nav((NAVItem('cash',10),),(NAVItem('debt',30),))
        self.assertEqual(r['equity'],-20)  # No second net-debt deduction; no zero floor.
    def test_negative_adjusted_asset_rejected(self):
        with self.assertRaises(ValueError):adjusted_nav((NAVItem('asset',1,-2),),())
    def test_duplicate_items_rejected(self):
        with self.assertRaises(ValueError):adjusted_nav((NAVItem('a',1),NAVItem('a',2)),())


class ExtendedExamplesTests(unittest.TestCase):
    def test_scenarios_match_blog(self):
        r=run_examples()
        for name,expected in [('conservative',36.39220572157432),('base',66.44468226943198),('optimistic',84.24961851120791)]:
            self.assertAlmostEqual(r['scenarios'][name]['equity'],expected,places=8)
    def test_sensitivity_center_and_monotonicity(self):
        table=run_examples()['sensitivity']['equity']
        self.assertAlmostEqual(table[2][2],66.44468226943198)
        self.assertTrue(all(row[i]<row[i+1] for row in table for i in range(4)))
        self.assertTrue(all(table[i][j]>table[i+1][j] for i in range(4) for j in range(5)))


if __name__=='__main__':unittest.main()
