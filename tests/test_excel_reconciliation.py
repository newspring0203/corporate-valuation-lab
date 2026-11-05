"""Read-only reconciliation of cached XLSX values; no Excel engine required.

The workbook stays local by request. Skip explicitly when absent on GitHub.
This validates the supplied saved snapshot, not recalculation after editing it.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from valuation_lab.example import run_examples

WORKBOOK=Path(__file__).resolve().parents[1]/'excel'/'A_company_valuation.xlsx'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


@unittest.skipUnless(WORKBOOK.exists(),'Local Excel workbook is intentionally not published')
class ExcelReconciliationTests(unittest.TestCase):
    def test_cached_values_and_formulas(self):
        r=run_examples()
        specs={1:{'D5':r['dcf']['ev'],'D7':r['dcf']['equity'],'D34':0},
               2:{'E5':r['comps']['equity_ev_ebitda'],'E6':r['comps']['equity_per']},
               3:{'D6':r['nav']['equity'],'D28':0}}
        for i,row in enumerate(r['dcf']['rows']):
            for col,val in [('13',row['revenue']),('20',row['fcff']),('22',row['pv'])]:
                specs[1][chr(70+i)+col]=val
        with ZipFile(WORKBOOK) as z:
            for sheet,expected in specs.items():
                root=ET.fromstring(z.read(f'xl/worksheets/sheet{sheet}.xml'))
                cells={c.attrib['r']:c for c in root.findall('.//m:c',NS)}
                self.assertFalse(any(c.attrib.get('t')=='e' for c in cells.values()))
                for address,value in expected.items():
                    with self.subTest(sheet=sheet,address=address):
                        cell=cells[address]
                        self.assertIsNotNone(cell.find('m:f',NS))
                        self.assertAlmostEqual(float(cell.find('m:v',NS).text),value,places=8)


if __name__=='__main__':unittest.main()
