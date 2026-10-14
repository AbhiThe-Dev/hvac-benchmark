"""Registry of the sources behind parameter ranges and cell claims. READ = the passage was opened and read by the
researcher (research_notes/Hot water recirculation diagnostic inputs/); SNIPPET = seen only in a search summary,
so it can back an ANALYST claim but never a SOURCE-provenance cell."""

SOURCES = {
    "PGE24": ("Zeyghami & Zhang, ACEEE SSB 2024, PG&E lab rig: risers balanced above 0.25 gpm/riser, none below 0.1; balanced risers within 2-5 F", "READ",
              "https://aceee.org/sites/default/files/proceedings/ssb24/pdfs/Best%20Practices%20for%20Hot%20Water%20Distribution%20Systems%20in%20Multifamily%20Buildings-A%20Comparative%20Evaluation%20of%20Balancing%20Methods.pdf"),
    "ETCC": ("ETCC multifamily DHW recirculation survey: loss 24.1-99.9 W per apartment (mean 62.5), 1.1-2.3x idealized", "READ", "https://etcc-ca.com/reports/multifamily-domestic-hot-water-recirculation-survey"),
    "BPA22": ("Ecotope for BPA 2022: Seattle UA multipliers 1.35 and 1.95", "READ", "https://www.bpa.gov/-/media/Aep/energy-efficiency/emerging-technologies/20220506-DHW-Distribution-Heat-Loss---Task-7.pdf"),
    "BED15": ("Bedard et al. 2015, Water Research 71: stagnation cool-down, principal return masks starved subordinate loops, logging beats spot readings", "READ",
              "https://espace.inrs.ca/id/eprint/3147/1/Bedard2015_Manuscript_Temperature%20Diagnostic.pdf"),
    "AYALA16": ("Ayala & Zobrist, ACEEE 2016: crossover detection methods, 52% of ~100 CA multifamily buildings", "READ", "https://www.aceee.org/files/proceedings/2016/data/papers/1_59.pdf"),
    "POWERS": ("Powers (Watts) TI430-420 Hi/Lo troubleshooting table: hot supply >= 25 F above set; liming/checkstop starvation; PRV differential", "READ",
               "https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/35401-source/6508945"),
    "CALEFFI": ("Caleffi 1164 ThermoSetter: Cv 0.35 min / 2.1 max, setpoint 105-150 F; GPM = BTU/h / (500 * dT)", "READ", "https://s3.amazonaws.com/s3.supplyhouse.com/product_files/Caleffi-116441AC-UserGuide.pdf"),
    "CDC": ("CDC Legionella control toolkit: storage >= 140 F, circulating >= 120 F", "READ", "https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html"),
    "VHA1061": ("VHA Directive 1061: distribution >= 124 F, storage >= 140 F, outlet <= 110 F", "READ", "https://www.va.gov/vhapublications/ViewPublication.asp?pub_ID=9181"),
    "HILLER": ("Plumbing Engineer (Hiller) via PHCP Pros: uninsulated 1/2-3/4 in copper 135->105 F in < 25 min; 120-130 F band; 1 min time-to-tap", "SNIPPET", "https://phcppros.com/articles/14203-legionella-cost-effective-control-part-3"),
    "PNNL21": ("PNNL-SA-156938: ASPE time-to-hot benchmarks (<=10 s, 11-30 s, >30 s) and dead-leg wait-time table", "READ", "https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-SA-156938.pdf"),
    "KLEIN": ("Klein / PHRC 2025: ~2x the pipe volume flows before water is hot", "READ", "https://www.phrc.psu.edu/assets/docs/Webinars/PHRC-Webinar_Best-Practices-for-High-Performance-Hot-Water-Systems_Handouts.pdf"),
    "FIELDPIECE": ("Fieldpiece pipe clamp: +-4 F as shipped, +-1 F after field calibration", "SNIPPET", "https://s3.amazonaws.com/s3.supplyhouse.com/product_files/ATC1-user.pdf"),
    "WATTS_ASSE": ("Watts ASSE comparison (2009): ASSE 1017 outlet tolerance +-3 to +-7 F by valve size", "READ", "https://www.watts.com/dfsmedia/0533dbba17714b1ab581ab07a4cbb521/18234-source/f-asse-stdcompare"),
    "BOCK": ("Bock, PHCP Pros 2024: fittings 30-50% of friction; balancing causes; velocity 2-3 ft/s", "READ", "https://www.phcppros.com/articles/19678-dhw-return-design-doing-it-right-and-the-risks-of-doing-it-wrong"),
    "HABITAT": ("Habitat 2019 Brooklyn case: reversed aquastat setpoints, pump never started", "READ", "https://www.habitatmag.com/Publication-Content/Bricks-Bucks/2019/2019-July/Valve-Fix"),
    "COOP": ("Cooperator: crossover and imbalance are sometimes confused", "READ", "https://cooperatornews.com/article/dont-get-your-building-into-hot-water"),
}
