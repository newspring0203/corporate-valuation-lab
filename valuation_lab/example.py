"""Fictional A-company inputs used in the blog, not observed company data."""
from dataclasses import replace
from .models import DCFInputs, NAVItem, Peer, dcf, comps, adjusted_nav

PEERS = (
    Peer('B',80,12.8,5,42.5,26.5,5,.02),
    Peer('C',120,19.2,9,85.5,30.1,10,.05),
    Peer('D',150,27,12,126,64.5,15,.08),
    Peer('E',180,39.6,18,216,120.8,20,.15),
)
ASSETS = (
    NAVItem('cash',10),NAVItem('receivables',15,-2),NAVItem('inventory',20,-3),
    NAVItem('other_operating_current_assets',5),NAVItem('land',30,20),
    NAVItem('plant',30,-4),NAVItem('intangible_assets',5),
)
LIABILITIES = (
    NAVItem('payables',15),NAVItem('other_operating_liabilities',5),
    NAVItem('interest_bearing_debt',30),NAVItem('unrecognized_obligation',0,4),
    NAVItem('assumed_net_deferred_tax_effect',0,2),
)


def run_examples():
    base=DCFInputs()
    # 08: tax and depreciation unchanged; retain scenario ratios at terminal.
    scenarios={
        'conservative':replace(base,growth_rates=(.04,.03,.03,.02,.02),ebit_margin=.10,capex_ratio=.055,nwc_ratio=.22),
        'base':base,
        'optimistic':replace(base,growth_rates=(.10,.08,.06,.05,.04),ebit_margin=.14,capex_ratio=.055,nwc_ratio=.19),
    }
    rates=(.10,.11,.12,.13,.14);growth=(.01,.015,.02,.025,.03)
    return dict(metadata=dict(case='Fictional A manufacturer',as_of='2025-12-31',
                             unit='KRW_100_million',equity_scope='100% common equity'),
                dcf=dcf(base),comps=comps(PEERS,16,7.5,20),nav=adjusted_nav(ASSETS,LIABILITIES),
                sensitivity=dict(wacc=rates,terminal_growth=growth,
                                 equity=[[dcf(replace(base,discount_rate=w,terminal_growth=g))['equity'] for g in growth] for w in rates]),
                scenarios={name:dcf(a) for name,a in scenarios.items()},
                fdd_illustration=dict(dcf=dcf(replace(base,additional_obligation=4)),
                                     normalized_ebitda=16+1-.5,
                                     ev_ebitda_equity=(16+1-.5)*6-20-4,
                                     per_after_normalization=None))
