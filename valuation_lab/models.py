"""Pure Python valuation functions with explicit input checks.

The caller must normalize currency, monetary units, dates and accounting scope
before passing numbers. Numerical checks do not establish economic validity.
"""
from dataclasses import dataclass
import math
from statistics import median
from typing import Optional, Sequence, Tuple


def finite(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def nonnegative(name, value):
    value = finite(name, value)
    if value < 0:
        raise ValueError(f'{name} must be nonnegative')
    return value


def fraction(name, value):
    value = finite(name, value)
    if not 0 <= value <= 1:
        raise ValueError(f'{name} must be between zero and one')
    return value


def wacc(cost_equity, cost_debt, tax_rate, equity_weight, debt_weight):
    """Assumed target market-value weights; not inferred from book equity."""
    ke = nonnegative('cost_equity', cost_equity)
    kd = nonnegative('cost_debt', cost_debt)
    tax = fraction('tax_rate', tax_rate)
    e = fraction('equity_weight', equity_weight)
    d = fraction('debt_weight', debt_weight)
    if not math.isclose(e + d, 1., rel_tol=0., abs_tol=1e-10):
        raise ValueError('capital weights must sum to one')
    return ke * e + kd * (1 - tax) * d


@dataclass(frozen=True)
class DCFInputs:
    revenue0: float = 100.
    nwc0: float = 20.
    growth_rates: Tuple[float, ...] = (.08, .06, .05, .04, .03)
    ebit_margin: float = .12
    tax_rate: float = .25
    da_ratio: float = .04
    capex_ratio: float = .05
    nwc_ratio: float = .20
    discount_rate: float = .12
    terminal_growth: float = .02
    # None means retain forecast operating ratios in the stable-growth year.
    terminal_ebit_margin: Optional[float] = None
    terminal_da_ratio: Optional[float] = None
    terminal_capex_ratio: Optional[float] = None
    terminal_nwc_ratio: Optional[float] = None
    net_debt: float = 20.
    additional_obligation: float = 0.


def dcf(inputs: DCFInputs):
    """End-year FCFF DCF with a separately rederived stable-growth year.

NOPAT uses EBIT*(1-tax), including a symmetric tax benefit for negative EBIT.
That convention is only an educational simplification, not a tax-loss model.
Additional obligation is a present-value amount excluded from FCFF/net debt.
"""
    if not isinstance(inputs, DCFInputs):
        raise ValueError('inputs must be DCFInputs')
    a = inputs
    revenue = finite('revenue0', a.revenue0)
    if revenue <= 0:
        raise ValueError('revenue0 must be positive')
    nwc = nonnegative('nwc0', a.nwc0)
    tax = fraction('tax_rate', a.tax_rate)
    margin = finite('ebit_margin', a.ebit_margin)
    da = nonnegative('da_ratio', a.da_ratio)
    capex = nonnegative('capex_ratio', a.capex_ratio)
    nwc_ratio = nonnegative('nwc_ratio', a.nwc_ratio)
    rate = finite('discount_rate', a.discount_rate)
    g = finite('terminal_growth', a.terminal_growth)
    if rate <= -1 or g <= -1 or rate <= g:
        raise ValueError('discount_rate must exceed terminal_growth; both must exceed -1')
    net_debt = finite('net_debt', a.net_debt)  # Can be negative for net cash.
    obligation = nonnegative('additional_obligation', a.additional_obligation)
    if not a.growth_rates:
        raise ValueError('at least one forecast period is required')
    growth = [finite('growth_rate', v) for v in a.growth_rates]
    if any(v <= -1 for v in growth):
        raise ValueError('growth_rate must exceed -1')
    rows = []
    for period, annual_growth in enumerate(growth, start=1):
        revenue *= 1 + annual_growth
        closing_nwc = revenue * nwc_ratio
        ebit = revenue * margin
        nopat = ebit * (1 - tax)
        depreciation, investment = revenue * da, revenue * capex
        increase = closing_nwc - nwc
        fcff = nopat + depreciation - investment - increase
        pv = fcff / (1 + rate) ** period
        rows.append(dict(period=period, growth=annual_growth, revenue=revenue,
                         ebit=ebit, nopat=nopat, depreciation=depreciation,
                         capex=investment, nwc=closing_nwc, delta_nwc=increase,
                         fcff=fcff, pv=pv))
        nwc = closing_nwc
    tm = margin if a.terminal_ebit_margin is None else finite('terminal_ebit_margin', a.terminal_ebit_margin)
    td = da if a.terminal_da_ratio is None else nonnegative('terminal_da_ratio', a.terminal_da_ratio)
    tc = capex if a.terminal_capex_ratio is None else nonnegative('terminal_capex_ratio', a.terminal_capex_ratio)
    tn = nwc_ratio if a.terminal_nwc_ratio is None else nonnegative('terminal_nwc_ratio', a.terminal_nwc_ratio)
    next_revenue = revenue * (1 + g)
    terminal_nwc = next_revenue * tn
    next_fcff = next_revenue * (tm * (1 - tax) + td - tc) - (terminal_nwc - nwc)
    terminal_value = next_fcff / (rate - g)
    terminal_pv = terminal_value / (1 + rate) ** len(rows)
    explicit_pv = math.fsum(row['pv'] for row in rows)
    ev = explicit_pv + terminal_pv
    equity_before_obligation = ev - net_debt
    result = dict(rows=rows, terminal_revenue=next_revenue, terminal_fcff=next_fcff,
                  terminal_value=terminal_value, terminal_pv=terminal_pv,
                  explicit_pv=explicit_pv, ev=ev, net_debt=net_debt,
                  additional_obligation=obligation,
                  equity_before_obligation=equity_before_obligation,
                  equity=equity_before_obligation - obligation)
    if not all(math.isfinite(v) for k,v in result.items() if k != 'rows'):
        raise ValueError('valuation result is not finite')
    return result


@dataclass(frozen=True)
class Peer:
    name: str
    revenue: float
    ebitda: float
    net_income: float
    equity: float
    debt: float
    excess_cash: float
    growth: float


def comps(peers: Sequence[Peer], target_ebitda, target_net_income, net_debt,
          additional_obligation=0.):
    """Median multiples are illustrative; comparable selection is external.

EV/EBITDA result is EV minus net debt and any present-value obligation.
PER directly produces equity: net debt is NEVER subtracted a second time.
A separately unrecognized obligation may require an additional adjustment;
whether it is already reflected in earnings/price requires external review.
"""
    if not peers:
        raise ValueError('at least one peer is required')
    names = [p.name for p in peers]
    if any(not isinstance(v,str) or not v.strip() for v in names) or len(set(names)) != len(names):
        raise ValueError('peer names must be nonempty and unique')
    rows = []
    for p in peers:
        rev = finite('peer revenue', p.revenue)
        eb = finite('peer EBITDA', p.ebitda)
        ni = finite('peer net income', p.net_income)
        if min(rev, eb, ni) <= 0:
            raise ValueError('this example requires positive peer revenue, EBITDA and net income')
        eq = nonnegative('peer equity', p.equity)
        debt = nonnegative('peer debt', p.debt)
        cash = nonnegative('peer excess_cash', p.excess_cash)
        growth = finite('peer growth', p.growth)
        ev = eq + debt - cash
        if ev <= 0:
            raise ValueError('this example requires positive peer EV')
        rows.append(dict(name=p.name, ev=ev, ev_ebitda=ev/eb, per=eq/ni,
                         ebitda_margin=eb/rev, growth=growth))
    te = nonnegative('target EBITDA', target_ebitda)
    ti = nonnegative('target net income', target_net_income)
    debt = finite('net_debt', net_debt)
    obligation = nonnegative('additional_obligation', additional_obligation)
    ev_multiple = median(r['ev_ebitda'] for r in rows)
    per_multiple = median(r['per'] for r in rows)
    ev = te * ev_multiple
    return dict(peers=rows, median_ev_ebitda=ev_multiple, median_per=per_multiple,
                ev=ev, equity_ev_ebitda=ev-debt-obligation,
                equity_per=ti*per_multiple-obligation)


@dataclass(frozen=True)
class NAVItem:
    name: str
    book_value: float
    adjustment: float = 0.


def adjusted_nav(assets: Sequence[NAVItem], liabilities: Sequence[NAVItem]):
    """Return equity directly; no subsequent net-debt deduction is applied."""
    if not assets:
        raise ValueError('at least one asset is required')
    def measure(items):
        names=[x.name for x in items]
        if any(not isinstance(n,str) or not n.strip() for n in names) or len(set(names))!=len(names):
            raise ValueError('item names must be nonempty and unique per group')
        rows=[]
        for item in items:
            book=nonnegative('book_value', item.book_value)
            adjustment=finite('adjustment', item.adjustment)
            if book+adjustment < 0:
                raise ValueError('adjusted asset/liability amount must be nonnegative')
            rows.append(dict(name=item.name,book=book,adjustment=adjustment,adjusted=book+adjustment))
        return rows
    ar,lr=measure(assets),measure(liabilities)
    ba,bl=math.fsum(r['book'] for r in ar),math.fsum(r['book'] for r in lr)
    aa,al=math.fsum(r['adjustment'] for r in ar),math.fsum(r['adjustment'] for r in lr)
    return dict(assets=ar,liabilities=lr,book_assets=ba,book_liabilities=bl,
                adjusted_assets=ba+aa,adjusted_liabilities=bl+al,
                book_equity=ba-bl,equity_adjustment=aa-al,equity=ba+aa-bl-al)
