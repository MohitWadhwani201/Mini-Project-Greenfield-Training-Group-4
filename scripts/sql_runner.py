
from pathlib import Path


def split_sql(text):
    
    statements, buffer, delimiter = [], [], ";"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(None, 1)[1].strip()
            continue
        if stripped.startswith("--"):
            continue
        if "--" in line:   
            before = line.split("--", 1)[0]
            if before.count("'") % 2 == 0:
                line = before.rstrip()
                stripped = line.strip()
        buffer.append(line)
        if stripped.endswith(delimiter):
            statement = "\n".join(buffer).strip()
            statement = statement[: -len(delimiter)].strip()
            if statement:
                statements.append(statement)
            buffer = []
    leftover = "\n".join(buffer).strip()
    if leftover:
        statements.append(leftover)
    return statements


def run_sql_file(connection, path):
    # Executes every statement of the file on an open SQLAlchemy connection; returns the count.
    statements = split_sql(Path(path).read_text(encoding="utf-8"))
    for statement in statements:
        connection.exec_driver_sql(statement.replace("%", "%%"))  # the MySQL driver treats a single % as a placeholder
    return len(statements)
