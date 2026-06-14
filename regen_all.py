"""
Batch-regenerate all QA reports (HTML + JSON + XLSX).
Run from the ibis_qa repo root:  python regen_all.py
"""
import subprocess, sys, os
from pathlib import Path

BASE  = Path(__file__).resolve().parent
IBIS  = Path(r"C:\Users\simonhwang_pcbauto\Desktop\IBIS Files")
HARK  = IBIS / r"Hark Labs\FPGA-MD-02047-1-1-CertusPro-NX-IBIS-AMI Model_file"
HARK2 = IBIS / r"Hark Labs\FPGA-MD-02115-1-0-Certus-NX-IBIS-AMI-File\FPGA-MD-02115-1-0-Certus-NX-IBIS-AMI-File\model_files"
MICRON = IBIS / "Micron"
TOOL  = BASE / "ibis_qa_tool" / "ibis_qa.py"
REPS  = BASE / "reports"

REPORTS = [
    # (ibs_path, stem, out_dir, plot_dir_or_None)
    (IBIS  / "Arbel_I3C_IBIS.ibs",
     "arbel",
     REPS / "ibis_files" / "arbel",
     REPS / "ibis_files" / "arbel" / "arbel_assets"),

    (HARK  / "abi_gen3.ibs",
     "hark_abi_gen3",
     REPS / "ibis_files" / "hark_abi_gen3",
     REPS / "ibis_files" / "hark_abi_gen3" / "hark_abi_gen3_assets"),

    (HARK  / "ibis_asg256_package_pin.ibs",
     "hark_asg256_package_pin",
     REPS / "ibis_files" / "hark_asg256_package_pin",
     None),

    (HARK  / "ibis_bbg484_package_pin.ibs",
     "hark_bbg484_package_pin",
     REPS / "ibis_files" / "hark_bbg484_package_pin",
     None),

    (HARK  / "ibis_bfg484_package_pin.ibs",
     "hark_bfg484_package_pin",
     REPS / "ibis_files" / "hark_bfg484_package_pin",
     None),

    (HARK  / "ibis_cbg256_package_pin.ibs",
     "hark_cbg256_package_pin",
     REPS / "ibis_files" / "hark_cbg256_package_pin",
     None),

    (HARK  / "ibis_jedi_fcbga67219012_rev_s_12_01_20_22u_820u_pcie_pin.ibs",
     "hark_jedi_fcbga672_pcie_pin",
     REPS / "ibis_files" / "hark_jedi_fcbga672_pcie_pin",
     None),

    (HARK  / "ibis_lattice_jedi_d1_80k_484cabga_12242020_latticeupdate_122520_12um_l2_3_pcie_pin.ibs",
     "hark_lattice_jedi_pcie_pin",
     REPS / "ibis_files" / "hark_lattice_jedi_pcie_pin",
     None),

    (HARK2 / "lfd2nx_ami_rx.ibs",
     "hark_lfd2nx_ami_rx",
     REPS / "ibis_files" / "hark_lfd2nx_ami_rx",
     REPS / "ibis_files" / "hark_lfd2nx_ami_rx" / "hark_lfd2nx_ami_rx_assets"),

    (HARK2 / "lfd2nx_ami_tx.ibs",
     "hark_lfd2nx_ami_tx",
     REPS / "ibis_files" / "hark_lfd2nx_ami_tx",
     REPS / "ibis_files" / "hark_lfd2nx_ami_tx" / "hark_lfd2nx_ami_tx_assets"),

    (HARK  / "ibis_lfg672_package_pin.ibs",
     "hark_lfg672_package_pin",
     REPS / "ibis_files" / "hark_lfg672_package_pin",
     None),

    (IBIS  / "Hibiki_IOCL_I3C_I2C_ibis_20260211.ibs",
     "hibiki",
     REPS / "ibis_files" / "hibiki",
     REPS / "ibis_files" / "hibiki" / "hibiki_assets"),

    (MICRON / "y32a.ibs",
     "y32a",
     REPS / "micron",
     REPS / "micron" / "y32a_assets"),

    (MICRON / "z41c-ibis" / "z41c.ibs",
     "z41c",
     REPS / "micron",
     REPS / "micron" / "z41c_assets"),

    (MICRON / "z41c-ibis" / "z41c_it.ibs",
     "z41c_it",
     REPS / "micron",
     REPS / "micron" / "z41c_it_assets"),
]

def run(ibs, stem, out_dir, plot_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    html_out = out_dir / f"{stem}.html"
    json_out = out_dir / f"{stem}.json"
    xlsx_out = out_dir / f"{stem}.xlsx"

    base_cmd = [sys.executable, str(TOOL), str(ibs), "--spreadsheet", str(xlsx_out)]
    if plot_dir:
        plot_dir.mkdir(parents=True, exist_ok=True)
        base_cmd += ["--plot-dir", str(plot_dir)]

    # HTML
    r = subprocess.run(base_cmd + ["--html"],
                       capture_output=True, cwd=str(BASE / "ibis_qa_tool"))
    if r.returncode != 0:
        print(f"  STDERR: {r.stderr.decode(errors='replace')[-500:]}")
    html_out.write_bytes(r.stdout)
    print(f"  HTML  -> {html_out}  ({len(r.stdout)//1024} KB)")

    # JSON
    r2 = subprocess.run(base_cmd + ["--json"],
                        capture_output=True, cwd=str(BASE / "ibis_qa_tool"))
    json_out.write_bytes(r2.stdout)
    print(f"  JSON  -> {json_out}  ({len(r2.stdout)//1024} KB)")


def main():
    for ibs, stem, out_dir, plot_dir in REPORTS:
        if not ibs.exists():
            print(f"[SKIP] {stem}: file not found — {ibs}")
            continue
        print(f"[{stem}]")
        run(ibs, stem, out_dir, plot_dir)
    print("\nDone.")

if __name__ == "__main__":
    main()
