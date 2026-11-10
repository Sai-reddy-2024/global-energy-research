"""Weekly European gas pipeline: pull GIE AGSI+, GIE ALSI and ENTSOG, rebuild the storage model and LNG balance, draft the weekly note.

Usage (run by .github/workflows/gas-weekly.yml every Friday, or by hand):
    python3 20261110_Code_Gas_Weekly_Pipeline_Europe_v01.py <ENERGY ANALYSIS folder> [--raw DIR] [--date YYYYMMDD] [--skip-pull]

Needs GIE_API_KEY in the environment (free key from agsi.gie.eu). ENTSOG needs no key.
Raw CSVs go to <raw> (default: 01.1_Raw_Data_Downloads/Other_Sources/API_<date>/, which is kept out of the public repo).
Outputs:
  01.4 .../<date>_Model_EU_Gas_Storage_Winter_Cases_Europe_Daily_v01.xlsx   (older dated copies move to 99_Archive)
  01.4 .../<date>_Model_EU_Gas_Storage_Latest_Paths_Europe_Daily_v01.csv
  03.4 .../<date>_Model_Global_LNG_Balance_Global_Quarterly_v01.xlsx         (older dated copies move to 99_Archive)
  08_Outputs/Reports/Weekly_Gas_Note/<date>_Analysis_Weekly_Gas_Note_Europe_Weekly_v01.md and three charts
The note compares actual storage with the paths of the live call (01.4 .../*_Model_EU_Gas_Storage_Call_Paths_*.csv, the newest one).
"""
import argparse, datetime as dt, glob, importlib.util, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def mod(fname):
    spec = importlib.util.spec_from_file_location(fname[:20], os.path.join(HERE, fname))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def archive_older(folder, pattern, keep, root, sub):
    dest = os.path.join(root, "99_Archive", sub); moved = []
    for f in sorted(glob.glob(os.path.join(folder, pattern))):
        if os.path.abspath(f) != os.path.abspath(keep):
            os.makedirs(dest, exist_ok=True); shutil.move(f, os.path.join(dest, os.path.basename(f))); moved.append(os.path.basename(f))
    return moved


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("root"); ap.add_argument("--raw"); ap.add_argument("--date"); ap.add_argument("--skip-pull", action="store_true")
    a = ap.parse_args(); root = a.root; date = a.date or dt.date.today().strftime("%Y%m%d")
    raw = a.raw or os.path.join(root, "01_Market_Foundations_and_Data/01.1_Raw_Data_Downloads/Other_Sources", "API_%s" % date)
    os.makedirs(raw, exist_ok=True)
    if not a.skip_pull:
        pull = mod("20261110_Code_Energy_Data_Pull_Global_v01.py")
        if not pull.GIE: sys.exit("Set GIE_API_KEY in the environment.")
        print("AGSI rows", pull.gie_pull(raw, date)); print("ALSI rows", pull.alsi_pull(raw, date)); print("ENTSOG rows", pull.entsog_pull(raw, date))
    bal = os.path.join(root, "01_Market_Foundations_and_Data/01.4_Supply_Demand_Balances")
    storage = mod("20261110_Code_Build_EU_Gas_Storage_Model_Europe_v01.py")
    out = os.path.join(bal, "%s_Model_EU_Gas_Storage_Winter_Cases_Europe_Daily_v01.xlsx" % date)
    latest = os.path.join(bal, "%s_Model_EU_Gas_Storage_Latest_Paths_Europe_Daily_v01.csv" % date)
    r = storage.build(root, raw, out, None, latest)
    for cs, p in r["paths"].items(): print("%-6s 31 Mar %.1f%%" % (cs, p[-1]["pct"]))
    print("archived", archive_older(bal, "*_Model_EU_Gas_Storage_Winter_Cases_Europe_Daily_v*.xlsx", out, root, "01.4_Supply_Demand_Balances"),
          archive_older(bal, "*_Model_EU_Gas_Storage_Latest_Paths_Europe_Daily_v*.csv", latest, root, "01.4_Supply_Demand_Balances"))
    tf = os.path.join(root, "03_Midstream_Logistics_and_Transportation/03.4_Trade_Flows_and_Sanctions")
    lng_out = os.path.join(tf, "%s_Model_Global_LNG_Balance_Global_Quarterly_v01.xlsx" % date)
    mod("20261110_Code_Build_Global_LNG_Balance_Global_v01.py").build(raw, lng_out)
    print("archived", archive_older(tf, "*_Model_Global_LNG_Balance_Global_Quarterly_v*.xlsx", lng_out, root, "03.4_Trade_Flows_and_Sanctions"))
    calls = sorted(glob.glob(os.path.join(bal, "*_Model_EU_Gas_Storage_Call_Paths_*.csv")))
    note_dir = os.path.join(root, "08_Outputs/Reports/Weekly_Gas_Note")
    print("note", mod("20261110_Code_Weekly_Gas_Note_Europe_v01.py").main(raw, calls[-1] if calls else latest, note_dir, date))


if __name__ == "__main__":
    main()
