from dataclasses import dataclass
import re
from pathlib import Path

from biomedical_api.core.config import get_settings


EXCLUDED_CATEGORY_PREFIXES = {"05_maintenance"}

PARAMETER_PATTERN = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
PARAMETER_COMMENT_PATTERN = re.compile(r"^//\s*:param\s+([A-Za-z_][A-Za-z0-9_]*)\s*=>\s*(.+?)\s*;?\s*$")


@dataclass(frozen=True, slots=True)
class CypherQueryDefinition:
    query_id: str
    category: str
    name: str
    description: str
    parameters: list[str]
    parameter_help: dict[str, str]
    path: Path

    @property
    def endpoint_path(self) -> str:
        return f"/api/v1/data/neo4j/queries/{self.query_id}"


class CypherQueryRepository:
    def __init__(self, query_root: Path | None = None) -> None:
        root = query_root or Path(get_settings().cypher_query_root)
        self.query_root = root

    def list_safe_queries(self) -> list[CypherQueryDefinition]:
        definitions: list[CypherQueryDefinition] = []
        if not self.query_root.exists():
            return definitions
        for category_dir in sorted(self.query_root.iterdir()):
            if not category_dir.is_dir():
                continue
            if category_dir.name in EXCLUDED_CATEGORY_PREFIXES:
                continue
            for path in sorted(category_dir.glob("*.cypher")):
                definitions.append(self._build_definition(path))
        return definitions

    def get_query(self, query_id: str) -> CypherQueryDefinition:
        for definition in self.list_safe_queries():
            if definition.query_id == query_id:
                return definition
        raise KeyError(query_id)

    def read_query_text(self, query_id: str) -> str:
        definition = self.get_query(query_id)
        return definition.path.read_text(encoding="utf-8")

    def _build_definition(self, path: Path) -> CypherQueryDefinition:
        relative_path = path.relative_to(self.query_root)
        category = relative_path.parts[0]
        query_id = "/".join(relative_path.with_suffix("").parts)
        contents = path.read_text(encoding="utf-8")
        description = self._extract_description(contents)
        parameter_help = self._extract_parameter_help(contents)
        parameters = sorted(set(PARAMETER_PATTERN.findall(contents)) | set(parameter_help))
        for parameter_name in parameters:
            parameter_help.setdefault(parameter_name, "Required Cypher parameter.")
        return CypherQueryDefinition(
            query_id=query_id,
            category=category,
            name=path.stem,
            description=description,
            parameters=parameters,
            parameter_help=parameter_help,
            path=path,
        )

    def _extract_description(self, contents: str) -> str:
        for line in contents.splitlines():
            stripped = line.strip()
            if stripped.startswith("//") and not stripped.startswith("// :param") and stripped != "// Parameters:":
                return stripped.removeprefix("//").strip()
        return ""

    def _extract_parameter_help(self, contents: str) -> dict[str, str]:
        parameter_help: dict[str, str] = {}
        for line in contents.splitlines():
            match = PARAMETER_COMMENT_PATTERN.match(line.strip())
            if match:
                parameter_help[match.group(1)] = match.group(2).strip()
        return parameter_help
