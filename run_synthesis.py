# Step 1: generates all synthetic data, checks its quality and writes the CSV files (no database needed).
import json
import logging
import sys
import time

import config
from synthesizer import (DataQualityValidator, DimDateGenerator, EmployeeSynthesizer,
                         RelatedDataSynthesizer, SCD2HistoryGenerator)


def main():
    # Runs the whole synthesis pipeline using the settings in config.py.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(message)s", datefmt="%H:%M:%S")
    log = logging.getLogger("run_synthesis")
    start_time = time.time()

    employees = EmployeeSynthesizer(config.RAW_IBM_CSV, config.TARGET_ROWS, config.REFERENCE_DATE,
                                    config.RANDOM_SEED, config.FAKER_LOCALE).scale()
    history = SCD2HistoryGenerator(employees, config.REFERENCE_DATE, config.SCD2_CHANGE_FRACTION,
                                   config.RANDOM_SEED).generate()
    related = RelatedDataSynthesizer(employees, config.REFERENCE_DATE, config.RANDOM_SEED)
    projects = related.generate_projects()
    assignments = related.generate_assignments(projects)
    reviews = related.generate_reviews()
    dim_date = DimDateGenerator().generate()

    results = DataQualityValidator(employees, history, projects, assignments, reviews, dim_date,
                                   min_rows=config.TARGET_ROWS).run()
    if not all(passed for _, passed, _ in results):
        log.error("Data-quality checks failed - no files written.")
        return 1

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tables = {"dim_date": dim_date, "employees": employees, "history": history,
              "projects": projects, "assignments": assignments, "reviews": reviews}
    manifest = {}
    for key, df in tables.items():
        path = config.OUTPUT_DIR / config.CSV_FILES[key]
        df.to_csv(path, index=False, date_format="%Y-%m-%d")
        manifest[config.CSV_FILES[key]] = len(df)
        log.info("Wrote %-28s %9s rows", path.name, f"{len(df):,}")
    (config.OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log.info("Done in %.1fs", time.time() - start_time)
    return 0


if __name__ == "__main__":
    sys.exit(main())
