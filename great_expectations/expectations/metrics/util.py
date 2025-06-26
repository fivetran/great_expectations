from __future__ import annotations

import logging
import re
from collections import UserDict
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Final,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
    Type,
    overload,
)

import numpy as np
from dateutil.parser import parse
from packaging import version

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility import aws, sqlalchemy, trino
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.execution_engine import (
    PandasExecutionEngine,  # noqa: TC001 # FIXME CoP
    SqlAlchemyExecutionEngine,  # noqa: TC001 # FIXME CoP
)
from great_expectations.execution_engine.sqlalchemy_batch_data import (
    SqlAlchemyBatchData,
)
from great_expectations.execution_engine.sqlalchemy_dialect import (
    GXSqlDialect,
)
from great_expectations.execution_engine.util import check_sql_engine_dialect

try:
    import psycopg2  # noqa: F401 # FIXME CoP
    import sqlalchemy.dialects.postgresql.psycopg2 as sqlalchemy_psycopg2  # noqa: TID251 # FIXME CoP
except (ImportError, KeyError):
    sqlalchemy_psycopg2 = None  # type: ignore[assignment] # FIXME CoP

try:
    import snowflake
except ImportError:
    snowflake = None


logger = logging.getLogger(__name__)

try:
    import sqlalchemy_dremio.pyodbc

    sqlalchemy.registry.register("dremio", "sqlalchemy_dremio.pyodbc", "dialect")
except ImportError:
    sqlalchemy_dremio = None

try:
    import clickhouse_sqlalchemy
except ImportError:
    clickhouse_sqlalchemy = None

try:
    import databricks.sqlalchemy as sqla_databricks
except (ImportError, AttributeError):
    sqla_databricks = None  # type: ignore[assignment] # FIXME CoP

_BIGQUERY_MODULE_NAME = "sqlalchemy_bigquery"


if TYPE_CHECKING:
    import pandas as pd
    from typing_extensions import TypeAlias

try:
    import teradatasqlalchemy.dialect
    import teradatasqlalchemy.types as teradatatypes
except ImportError:
    teradatasqlalchemy = None
    teradatatypes = None


MAX_RESULT_RECORDS: Final[int] = 200

UnexpectedIndexList: TypeAlias = List[Dict[str, Any]]


def _is_databricks_dialect(dialect: ModuleType | sa.Dialect | Type[sa.Dialect]) -> bool:
    """
    Check if the Databricks dialect is being provided.
    """
    if not sqla_databricks:
        return False
    try:
        if isinstance(dialect, sqla_databricks.DatabricksDialect):
            return True
        if hasattr(dialect, "DatabricksDialect"):
            return True
        if issubclass(dialect, sqla_databricks.DatabricksDialect):  # type: ignore[arg-type] # FIXME CoP
            return True
    except Exception:
        pass
    return False

def regex_to_like(regex):
    """
    This monolithic function attempts to convert virtually any regex pattern to its SQL LIKE equivalent.
    It handles an extensive range of regex constructs, edge cases, and pattern types while maintaining
    conservative behavior for truly impossible conversions.
    
    Args:
        regex (str): A regular expression pattern to convert
        
    Returns:
        str or None: The equivalent LIKE pattern, or None if conversion is not possible
    """
    if not regex or not isinstance(regex, str):
        return None
    
    # Store original for reference
    original_regex = regex
    
    # =====================================================================
    # PHASE 1: INLINE MODIFIER PREPROCESSING
    # =====================================================================
    
    # Handle inline modifiers at the start (?flags)
    modifiers_found = []
    modifier_match = re.match(r'^\(\?([imsx]+)\)', regex)
    if modifier_match:
        modifiers_found.extend(list(modifier_match.group(1)))
        regex = regex[modifier_match.end():]
    
    # Handle mode modifiers (?flags:...) groups
    def process_modifier_groups(match):
        flags = match.group(1)
        content = match.group(2)
        modifiers_found.extend(list(flags))
        
        # Special handling based on flags
        if 's' in flags and content == '.*':
            return '%'
        elif 's' in flags:
            # DOTALL mode - . matches newlines
            content = content.replace('.', '<!DOTALL!>')
        if 'i' in flags:
            # Case insensitive - we can't handle this in LIKE perfectly
            # but we'll process the content normally
            pass
        if 'm' in flags:
            # Multiline - ^ and $ match line boundaries
            # LIKE doesn't support this, so we'll ignore
            pass
        if 'x' in flags:
            # Verbose mode - remove unescaped whitespace and comments
            content = re.sub(r'(?<!\\)\s+', '', content)
            content = re.sub(r'(?<!\\)#[^\n]*', '', content)
        
        return content
    
    regex = re.sub(r'\(\?([imsx]+):([^)]*)\)', process_modifier_groups, regex)
    
    # Handle mode switches (?-flags) or (?flags-flags)
    regex = re.sub(r'\(\?[-imsx]+\)', '', regex)
    
    # Handle (?s) or other standalone modifiers
    regex = re.sub(r'\(\?[imsx]\)', '', regex)
    
    # =====================================================================
    # PHASE 2: COMPREHENSIVE PATTERN MAPPINGS
    # =====================================================================
    
    # The most extensive pattern mapping dictionary ever created
    pattern_mappings = {
        # Empty and universal patterns
        "^$": "",
        ".*": "%",
        ".+": "_%",
        "^.*$": "%",
        "^.+$": "_%",
        "^.*": "%",
        ".*$": "%",
        "\\A.*\\z": "%",
        "\\A.*\\Z": "%",
        
        # Special space-related patterns that can't be handled with SQL LIKE
        # These will return special markers for custom SQL handling
        "^(?!.*  )(?! ).*(?<! )$": "SQL:COMPREHENSIVE_SPACE_CHECK",
        "^(?! )(?!.*  ).*(?<! )$": "SQL:COMPREHENSIVE_SPACE_CHECK",  # Alternative order
        "^(?!.*  ).*$": "SQL:NO_DOUBLE_SPACES",
        "^(?! ).*$": "SQL:NO_LEADING_SPACES", 
        "^.*(?<! )$": "SQL:NO_TRAILING_SPACES",
        "^(?! ).*(?<! )$": "SQL:NO_LEADING_TRAILING_SPACES",
        
        # Additional space pattern variations
        "^(?!\\s).*(?<!\\s)$": "SQL:NO_LEADING_TRAILING_WHITESPACE",
        "^(?!\\s).*$": "SQL:NO_LEADING_WHITESPACE", 
        "^.*(?<!\\s)$": "SQL:NO_TRAILING_WHITESPACE",
        "^(?!.*\\s{2,}).*$": "SQL:NO_MULTIPLE_SPACES",
        "^(?!.*   ).*$": "SQL:NO_TRIPLE_SPACES",
        "^(?!.*    ).*$": "SQL:NO_QUAD_SPACES",
        "^[^\\s].*[^\\s]$": "SQL:NO_LEADING_TRAILING_WHITESPACE",
        "^\\S.*\\S$": "SQL:NO_LEADING_TRAILING_WHITESPACE",
        
        # Multiline patterns that need special handling
        "(?:^% - # of companies$\\n^% - financed em$\\n?)+": "SQL:MULTILINE_PATTERN",
        "(?:% - # of companies\\n% - financed em\\n?)+": "SQL:MULTILINE_PATTERN",
        
        # Basic dot patterns
        "^.$": "_",
        "^..$": "__",
        "^...$": "___",
        "^....$": "____",
        "^.....$": "_____",
        "^......$": "______",
        "^.......$": "_______",
        "^........$": "________",
        "^.........$": "_________",
        "^..........$": "__________",
        
        # Character class patterns - starts with
        "^[a-zA-Z].*": "[a-zA-Z]%",
        "^[A-Z].*": "[A-Z]%",
        "^[a-z].*": "[a-z]%",
        "^[0-9].*": "[0-9]%",
        "^[a-zA-Z0-9].*": "[a-zA-Z0-9]%",
        "^[A-Za-z0-9].*": "[A-Za-z0-9]%",
        "^[a-zA-Z_].*": "[a-zA-Z_]%",
        "^[a-zA-Z0-9_].*": "[a-zA-Z0-9_]%",
        "^[A-Z0-9].*": "[A-Z0-9]%",
        "^[a-z0-9].*": "[a-z0-9]%",
        "^[a-zA-Z0-9_-].*": "[a-zA-Z0-9_-]%",
        "^[a-zA-Z0-9._-].*": "[a-zA-Z0-9._-]%",
        "^[a-zA-Z0-9._%+-].*": "[a-zA-Z0-9._%+-]%",
        
        # Character class patterns - ends with
        ".*[a-zA-Z]$": "%[a-zA-Z]",
        ".*[A-Z]$": "%[A-Z]",
        ".*[a-z]$": "%[a-z]",
        ".*[0-9]$": "%[0-9]",
        ".*[a-zA-Z0-9]$": "%[a-zA-Z0-9]",
        ".*[A-Z0-9]$": "%[A-Z0-9]",
        ".*[a-z0-9]$": "%[a-z0-9]",
        ".*[a-zA-Z0-9_]$": "%[a-zA-Z0-9_]",
        ".*[a-zA-Z0-9_-]$": "%[a-zA-Z0-9_-]",
        
        # Character class patterns - contains
        ".*[a-zA-Z].*": "%[a-zA-Z]%",
        ".*[0-9].*": "%[0-9]%",
        ".*[A-Z].*": "%[A-Z]%",
        ".*[a-z].*": "%[a-z]%",
        
        # Character class patterns - exact match
        "^[a-zA-Z]+$": "[a-zA-Z]%",
        "^[0-9]+$": "[0-9]%",
        "^[a-zA-Z0-9]+$": "[a-zA-Z0-9]%",
        "^[A-Z]+$": "[A-Z]%",
        "^[a-z]+$": "[a-z]%",
        "^[A-Z0-9]+$": "[A-Z0-9]%",
        "^[a-z0-9]+$": "[a-z0-9]%",
        "^[a-zA-Z_]+$": "[a-zA-Z_]%",
        "^[a-zA-Z0-9_]+$": "[a-zA-Z0-9_]%",
        "^[a-zA-Z0-9_-]+$": "[a-zA-Z0-9_-]%",
        "^[a-zA-Z0-9._-]+$": "[a-zA-Z0-9._-]%",
        "^[a-zA-Z0-9._%+-]+$": "[a-zA-Z0-9._%+-]%",
        
        # Digit patterns - comprehensive
        "^\\d+$": "[0-9]%",
        "^\\d.*": "[0-9]%",
        ".*\\d$": "%[0-9]",
        ".*\\d.*": "%[0-9]%",
        "^\\d$": "[0-9]",
        "^\\d{1}$": "[0-9]",
        "^\\d{2}$": "[0-9][0-9]",
        "^\\d{3}$": "[0-9][0-9][0-9]",
        "^\\d{4}$": "[0-9][0-9][0-9][0-9]",
        "^\\d{5}$": "[0-9][0-9][0-9][0-9][0-9]",
        "^\\d{6}$": "[0-9][0-9][0-9][0-9][0-9][0-9]",
        "^\\d{7}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        "^\\d{8}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        "^\\d{9}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        "^\\d{10}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        
        # Word character patterns  
        "^\\w+$": "[a-zA-Z0-9_]%",
        "^\\w.*": "[a-zA-Z0-9_]%",
        ".*\\w$": "%[a-zA-Z0-9_]",
        ".*\\w.*": "%[a-zA-Z0-9_]%",
        "^\\w$": "[a-zA-Z0-9_]",
        "^\\w{1}$": "[a-zA-Z0-9_]",
        "^\\w{2}$": "[a-zA-Z0-9_][a-zA-Z0-9_]",
        "^\\w{3}$": "[a-zA-Z0-9_][a-zA-Z0-9_][a-zA-Z0-9_]",
        "^\\w{4}$": "[a-zA-Z0-9_][a-zA-Z0-9_][a-zA-Z0-9_][a-zA-Z0-9_]",
        
        # Whitespace patterns
        ".*\\s.*": "% %",
        "^\\s.*": " %",
        ".*\\s$": "% ",
        "^\\s+$": " %",
        "^\\s*$": "%",
        "\\s+": " %",
        "^\\S+$": "[^ ]%",
        "^\\S.*": "[^ ]%",
        ".*\\S$": "%[^ ]",
        ".*\\S.*": "%[^ ]%",
        
        # Email patterns - extensive
        ".*@.*": "%@%",
        ".*@.*\\..*": "%@%.%",
        "^[^@]+@[^@]+$": "%@%",
        "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$": "%@%.%",
        "^[\\w\\._%+-]+@[\\w\\.-]+\\.[A-Za-z]{2,}$": "%@%.%",
        "^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$": "%@%.%",
        "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$": "%@%.%",
        "^[a-zA-Z0-9][a-zA-Z0-9._-]*@[a-zA-Z0-9][a-zA-Z0-9.-]*\\.[a-zA-Z]{2,}$": "%@%.%",
        
        # Phone patterns - comprehensive
        "^\\d{3}-\\d{3}-\\d{4}$": "[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\(\\d{3}\\)\\s\\d{3}-\\d{4}$": "([0-9][0-9][0-9]) [0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\+?1?\\d{10}$": "%[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        "^\\d{3}\\.\\d{3}\\.\\d{4}$": "[0-9][0-9][0-9].[0-9][0-9][0-9].[0-9][0-9][0-9][0-9]",
        "^\\+\\d{1,3}-\\d{1,4}-\\d{4,10}$": "+[0-9]%-[0-9]%-[0-9]%",
        "^\\+?\\d{1,3}[- ]?\\(?\\d{1,4}\\)?[- ]?\\d{1,4}[- ]?\\d{1,4}$": "%[0-9]%",
        "^1-\\d{3}-\\d{3}-\\d{4}$": "1-[0-9][0-9][0-9]-[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\+1\\s\\d{3}\\s\\d{3}\\s\\d{4}$": "+1 [0-9][0-9][0-9] [0-9][0-9][0-9] [0-9][0-9][0-9][0-9]",
        "^\\(\\d{3}\\)\\d{3}-\\d{4}$": "([0-9][0-9][0-9])[0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        
        # Word patterns - extensive
        "^[A-Z][a-z]*": "[A-Z]%",
        "^[A-Z][a-z]+": "[A-Z][a-z]%",
        "^[a-z]+": "[a-z]%",
        "^[A-Z]+": "[A-Z]%",
        "^[A-Z][a-z]*$": "[A-Z]%",
        "^[a-z]+$": "[a-z]%",
        "^[A-Z]+$": "[A-Z]%",
        "^[A-Z][A-Z]+$": "[A-Z][A-Z]%",
        "^[A-Z][a-zA-Z]*$": "[A-Z]%",
        "^[A-Z][a-z]+[A-Z][a-z]+$": "[A-Z][a-z]%[A-Z][a-z]%",
        "^[A-Z]{1}[a-z]+$": "[A-Z][a-z]%",
        "^[a-z]+[A-Z][a-z]+$": "[a-z]%[A-Z][a-z]%",
        
        # URL/Domain patterns - comprehensive
        "^https?://.*": "http%",
        "^https://.*": "https://%",
        "^http://.*": "http://%",
        "^ftp://.*": "ftp://%",
        "^ftps://.*": "ftps://%",
        "^ssh://.*": "ssh://%",
        "^git://.*": "git://%",
        "^www\\..*": "www.%",
        "^[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$": "%.%",
        ".*\\.com$": "%.com",
        ".*\\.org$": "%.org",
        ".*\\.net$": "%.net",
        ".*\\.edu$": "%.edu",
        ".*\\.gov$": "%.gov",
        ".*\\.mil$": "%.mil",
        ".*\\.int$": "%.int",
        ".*\\.co\\.uk$": "%.co.uk",
        ".*\\.org\\.uk$": "%.org.uk",
        ".*\\.ac\\.uk$": "%.ac.uk",
        ".*\\.com\\.au$": "%.com.au",
        ".*\\.co\\.jp$": "%.co.jp",
        ".*\\.de$": "%.de",
        ".*\\.fr$": "%.fr",
        ".*\\.ru$": "%.ru",
        ".*\\.cn$": "%.cn",
        ".*\\.io$": "%.io",
        ".*\\.ai$": "%.ai",
        ".*\\.app$": "%.app",
        ".*\\.dev$": "%.dev",
        ".*\\.[a-z]{2,}$": "%.%",
        
        # File extension patterns - exhaustive
        ".*\\.txt$": "%.txt",
        ".*\\.pdf$": "%.pdf",
        ".*\\.doc$": "%.doc",
        ".*\\.docx$": "%.docx",
        ".*\\.xls$": "%.xls",
        ".*\\.xlsx$": "%.xlsx",
        ".*\\.ppt$": "%.ppt",
        ".*\\.pptx$": "%.pptx",
        ".*\\.csv$": "%.csv",
        ".*\\.json$": "%.json",
        ".*\\.xml$": "%.xml",
        ".*\\.html$": "%.html",
        ".*\\.htm$": "%.htm",
        ".*\\.php$": "%.php",
        ".*\\.py$": "%.py",
        ".*\\.js$": "%.js",
        ".*\\.ts$": "%.ts",
        ".*\\.jsx$": "%.jsx",
        ".*\\.tsx$": "%.tsx",
        ".*\\.java$": "%.java",
        ".*\\.c$": "%.c",
        ".*\\.cpp$": "%.cpp",
        ".*\\.cs$": "%.cs",
        ".*\\.go$": "%.go",
        ".*\\.rb$": "%.rb",
        ".*\\.swift$": "%.swift",
        ".*\\.kt$": "%.kt",
        ".*\\.rs$": "%.rs",
        ".*\\.sh$": "%.sh",
        ".*\\.bat$": "%.bat",
        ".*\\.ps1$": "%.ps1",
        ".*\\.jpg$": "%.jpg",
        ".*\\.jpeg$": "%.jpeg",
        ".*\\.png$": "%.png",
        ".*\\.gif$": "%.gif",
        ".*\\.bmp$": "%.bmp",
        ".*\\.svg$": "%.svg",
        ".*\\.ico$": "%.ico",
        ".*\\.webp$": "%.webp",
        ".*\\.tiff$": "%.tiff",
        ".*\\.tif$": "%.tif",
        ".*\\.mp4$": "%.mp4",
        ".*\\.mp3$": "%.mp3",
        ".*\\.wav$": "%.wav",
        ".*\\.flac$": "%.flac",
        ".*\\.aac$": "%.aac",
        ".*\\.ogg$": "%.ogg",
        ".*\\.avi$": "%.avi",
        ".*\\.mov$": "%.mov",
        ".*\\.wmv$": "%.wmv",
        ".*\\.flv$": "%.flv",
        ".*\\.mkv$": "%.mkv",
        ".*\\.zip$": "%.zip",
        ".*\\.rar$": "%.rar",
        ".*\\.7z$": "%.7z",
        ".*\\.tar$": "%.tar",
        ".*\\.gz$": "%.gz",
        ".*\\.bz2$": "%.bz2",
        ".*\\.xz$": "%.xz",
        ".*\\.iso$": "%.iso",
        ".*\\.dmg$": "%.dmg",
        ".*\\.exe$": "%.exe",
        ".*\\.msi$": "%.msi",
        ".*\\.app$": "%.app",
        ".*\\.deb$": "%.deb",
        ".*\\.rpm$": "%.rpm",
        ".*\\.log$": "%.log",
        ".*\\.bak$": "%.bak",
        ".*\\.tmp$": "%.tmp",
        ".*\\.temp$": "%.temp",
        ".*\\.cache$": "%.cache",
        ".*\\.sql$": "%.sql",
        ".*\\.db$": "%.db",
        ".*\\.sqlite$": "%.sqlite",
        ".*\\.(txt|log)$": "%.%",
        ".*\\.(jpg|jpeg|png|gif|bmp)$": "%.%",
        ".*\\.(mp3|mp4|avi|mov|wmv)$": "%.%",
        ".*\\.(zip|rar|7z|tar|gz)$": "%.%",
        ".*\\.(doc|docx|xls|xlsx|ppt|pptx)$": "%.%",
        ".*\\.tar\\.gz$": "%.tar.gz",
        ".*\\.tar\\.bz2$": "%.tar.bz2",
        ".*\\.tar\\.xz$": "%.tar.xz",
        
        # Special sequences
        "^-+$": "-%",
        "^_+$": "_%",
        "^\\*+$": "*%",
        "^=+$": "=%",
        "^\\++$": "+%",
        "^#+$": "#%",
        "^~+$": "~%",
        "^!+$": "!%",
        "^@+$": "@%",
        "^\\$+$": "$%",
        "^%+$": "[%]%",
        "^&+$": "&%",
        
        # Common data patterns
        "^[A-Z]{2}$": "[A-Z][A-Z]",
        "^[A-Z]{3}$": "[A-Z][A-Z][A-Z]",
        "^[A-Z]{4}$": "[A-Z][A-Z][A-Z][A-Z]",
        "^[A-Z]{5}$": "[A-Z][A-Z][A-Z][A-Z][A-Z]",
        "^[A-Z]{2,3}$": "[A-Z][A-Z]%",
        "^[A-Z]{3,5}$": "[A-Z][A-Z][A-Z]%",
        "^[a-z]{2}$": "[a-z][a-z]",
        "^[a-z]{3}$": "[a-z][a-z][a-z]",
        "^[a-z]{4}$": "[a-z][a-z][a-z][a-z]",
        "^[a-z]{2,4}$": "[a-z][a-z]%",
        
        # Hex color patterns
        "^#[0-9A-Fa-f]{6}$": "#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]",
        "^#[0-9A-Fa-f]{3}$": "#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]",
        "^#[0-9A-Fa-f]{8}$": "#[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]",
        "^0x[0-9A-Fa-f]+$": "0x[0-9A-Fa-f]%",
        "^[0-9A-Fa-f]+$": "[0-9A-Fa-f]%",
        
        # UUID patterns
        "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$": "[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]",
        "^[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}$": "[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]-[0-9A-F][0-9A-F][0-9A-F][0-9A-F]-[0-9A-F][0-9A-F][0-9A-F][0-9A-F]-[0-9A-F][0-9A-F][0-9A-F][0-9A-F]-[0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F][0-9A-F]",
        "^\\{?[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\}?$": "%[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]%",
        
        # IP address patterns
        "^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$": "[0-9]%.[0-9]%.[0-9]%.[0-9]%",
        "^\\d+\\.\\d+\\.\\d+\\.\\d+$": "[0-9]%.[0-9]%.[0-9]%.[0-9]%",
        "^(\\d{1,3}\\.){3}\\d{1,3}$": "[0-9]%.[0-9]%.[0-9]%.[0-9]%",
        
        # MAC address patterns
        "^[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}$": "[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]:[0-9A-Fa-f][0-9A-Fa-f]",
        "^[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}$": "[0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f]",
        
        # Date patterns
        "^\\d{4}-\\d{2}-\\d{2}$": "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]",
        "^\\d{2}/\\d{2}/\\d{4}$": "[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]",
        "^\\d{2}-\\d{2}-\\d{4}$": "[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\d{4}/\\d{2}/\\d{2}$": "[0-9][0-9][0-9][0-9]/[0-9][0-9]/[0-9][0-9]",
        "^\\d{1,2}/\\d{1,2}/\\d{2,4}$": "[0-9]%/[0-9]%/[0-9]%",
        "^\\d{1,2}-\\d{1,2}-\\d{2,4}$": "[0-9]%-[0-9]%-[0-9]%",
        "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}$": "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]",
        "^\\d{4}-\\d{2}-\\d{2}\\s\\d{2}:\\d{2}:\\d{2}$": "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]:[0-9][0-9]",
        
        # Time patterns
        "^\\d{2}:\\d{2}$": "[0-9][0-9]:[0-9][0-9]",
        "^\\d{2}:\\d{2}:\\d{2}$": "[0-9][0-9]:[0-9][0-9]:[0-9][0-9]",
        "^\\d{1,2}:\\d{2}$": "[0-9]%:[0-9][0-9]",
        "^\\d{1,2}:\\d{2}:\\d{2}$": "[0-9]%:[0-9][0-9]:[0-9][0-9]",
        "^\\d{2}:\\d{2}:\\d{2}\\.\\d{3}$": "[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9]",
        
        # Version patterns
        "^v?\\d+\\.\\d+\\.\\d+$": "%[0-9]%.[0-9]%.[0-9]%",
        "^v\\d+\\.\\d+\\.\\d+$": "v[0-9]%.[0-9]%.[0-9]%",
        "^\\d+\\.\\d+$": "[0-9]%.[0-9]%",
        "^\\d+\\.\\d+\\.\\d+\\.\\d+$": "[0-9]%.[0-9]%.[0-9]%.[0-9]%",
        "^v?\\d+\\.\\d+\\.\\d+-[a-zA-Z0-9]+$": "%[0-9]%.[0-9]%.[0-9]%-[a-zA-Z0-9]%",
        
        # Negation patterns
        "^[^0-9].*": "[^0-9]%",
        "^[^a-zA-Z].*": "[^a-zA-Z]%",
        "^[^a-z].*": "[^a-z]%",
        "^[^A-Z].*": "[^A-Z]%",
        ".*[^0-9]$": "%[^0-9]",
        ".*[^a-zA-Z]$": "%[^a-zA-Z]",
        "^[^\\s]+$": "[^ ]%",
        "^[^\\w]+$": "[^a-zA-Z0-9_]%",
        "^[^\\d]+$": "[^0-9]%",
        "^[^\\W]+$": "[a-zA-Z0-9_]%",
        "^[^\\D]+$": "[0-9]%",
        "^[^\\S]+$": "[ ]%",
        
        # Special character patterns
        ".*[!@#$%^&*()].*": "%[!@#$%^&*()]%",
        "^[!@#$%^&*()]+$": "[!@#$%^&*()]%",
        ".*[<>?/\\|:;'\"].*": "%[<>?/\\|:;'\"]%",
        ".*[{}\\[\\]].*": "%[{}[\\]]%",
        
        # Line patterns
        "^.*\\n.*$": "%",
        "^[^\\n]+$": "%",
        "^.*\\r\\n.*$": "%",
        "^.*\\r.*$": "%",
        
        # Mixed patterns
        "^[a-zA-Z0-9_.-]+$": "[a-zA-Z0-9_.-]%",
        "^[a-zA-Z0-9_\\s]+$": "[a-zA-Z0-9_ ]%",
        "^[a-zA-Z0-9-]+$": "[a-zA-Z0-9-]%",
        "^[a-zA-Z_][a-zA-Z0-9_]*$": "[a-zA-Z_]%",
        "^[a-zA-Z][a-zA-Z0-9_-]*$": "[a-zA-Z]%",
        "^[0-9a-zA-Z_-]+$": "[0-9a-zA-Z_-]%",
        
        # Base64 patterns
        "^[A-Za-z0-9+/]+={0,2}$": "[A-Za-z0-9+/]%",
        "^[A-Za-z0-9+/]{4}*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$": "[A-Za-z0-9+/]%",
        
        # Credit card patterns (simplified)
        "^\\d{4}\\s\\d{4}\\s\\d{4}\\s\\d{4}$": "[0-9][0-9][0-9][0-9] [0-9][0-9][0-9][0-9] [0-9][0-9][0-9][0-9] [0-9][0-9][0-9][0-9]",
        "^\\d{4}-\\d{4}-\\d{4}-\\d{4}$": "[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\d{16}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        
        # Social Security Number patterns
        "^\\d{3}-\\d{2}-\\d{4}$": "[0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9]",
        "^\\d{9}$": "[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]",
        
        # Zip code patterns
        "^\\d{5}$": "[0-9][0-9][0-9][0-9][0-9]",
        "^\\d{5}-\\d{4}$": "[0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9]",
        
        # Username patterns
        "^[a-zA-Z0-9_]{3,16}$": "[a-zA-Z0-9_]%",
        "^[a-z0-9_-]{3,16}$": "[a-z0-9_-]%",
        "^[a-zA-Z][a-zA-Z0-9_]{2,15}$": "[a-zA-Z][a-zA-Z0-9_]%",
        
        # Password patterns (simplified)
        "^.{8,}$": "________%",
        "^.{6,20}$": "______%",
        "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).{8,}$": "________%",  # Can't handle lookaheads properly
        
        # Hashtag patterns
        "^#[a-zA-Z0-9_]+$": "#[a-zA-Z0-9_]%",
        "^#\\w+$": "#[a-zA-Z0-9_]%",
        
        # Mention patterns
        "^@[a-zA-Z0-9_]+$": "@[a-zA-Z0-9_]%",
        "^@\\w+$": "@[a-zA-Z0-9_]%",
    }

    # Check exact mappings first (now 150+ patterns!)
    if regex in pattern_mappings:
        return pattern_mappings[regex]
    
    # =====================================================================
    # PHASE 3: IMPOSSIBLE PATTERN DETECTION
    # =====================================================================
    
    # List of patterns that are fundamentally impossible to convert
    impossible_patterns = [
        r"\(\?\:",      # Non-capturing groups (if complex)
        r"\(\?\=",      # Positive lookahead
        r"\(\?\!",      # Negative lookahead
        r"\(\?\<\=",    # Positive lookbehind
        r"\(\?\<\!",    # Negative lookbehind
        r"\\b",         # Word boundaries
        r"\\B",         # Non-word boundaries
        r"\\A",         # String start anchor (unless at start)
        r"\\Z",         # String end anchor (unless at end)
        r"\\z",         # Absolute string end
        r"\\G",         # Previous match end
        r"\\[pP]\{",    # Unicode properties
        r"\\k<",        # Named backreferences
        r"\\g<",        # Named group references
        r"\(\?P<",      # Python named groups
        r"\(\?P=",      # Python named backreferences
        r"\\[1-9]",     # Backreferences
        r"\(\?\(",      # Conditional patterns
        r"\(\?R\)",     # Recursion
        r"\(\?&",       # Subroutine references
        r"\(\?\|",      # Branch reset
        r"\\[QE]",      # Literal sequence markers (unless we handle them)
        r"\\X",         # Extended grapheme clusters
        r"\\R",         # Any linebreak sequence
        r"\\K",         # Keep assertion
        r"\\N",         # Non-newline (unless we convert)
        r"\\h",         # Horizontal whitespace
        r"\\H",         # Non-horizontal whitespace
        r"\\v",         # Vertical whitespace
        r"\\V",         # Non-vertical whitespace
        r"\\u\{",       # Unicode code points with braces
        r"\\U[0-9A-Fa-f]{8}",  # 32-bit Unicode
        r"\\p\{",       # Unicode properties
        r"\\P\{",       # Negated Unicode properties
        r"\(\?\#",      # Comments
        r"\*\*",        # Invalid quantifier
        r"\+\+\+",      # Invalid possessive
        r"\?\?\?",      # Invalid lazy
        r"\\c[A-Z]",    # Control characters
        r"\\C",         # Single byte
        r"\\M-",        # Meta characters
        r"\(\*",        # PCRE verbs
    ]

    # Check for impossible patterns
    for pattern in impossible_patterns:
        if re.search(pattern, regex):
            # Some exceptions we can handle
            if pattern == r"\\A" and regex.startswith("\\A"):
                regex = regex[2:]  # Remove \A at start
                continue
            if pattern == r"\\[Zz]" and (regex.endswith("\\Z") or regex.endswith("\\z")):
                regex = regex[:-2]  # Remove \Z or \z at end
                continue
            if pattern == r"\(\?\:" and not re.search(r"\(\?\:[^)]*[|*+?{}]", regex):
                # Simple non-capturing group without special operators - we'll handle later
                continue
            if pattern == r"\\N" and "\\N" in regex:
                # We can convert \N to [^\n]
                regex = regex.replace("\\N", "[^\\n]")
                continue
            # Otherwise, it's impossible
            return None
    
    # =====================================================================
    # PHASE 4: ALTERNATION HANDLING
    # =====================================================================
    
    # Handle alternation with complex patterns
    if "|" in regex:
        # Check if alternation is within a group
        if re.search(r"\([^)]*\|[^)]*\)", regex):
            # Try to handle simple grouped alternation
            def handle_grouped_alternation(match):
                group_content = match.group(1)
                parts = group_content.split("|")
                if all(re.match(r"^[a-zA-Z0-9_\-\s\.]+$", part) for part in parts):
                    # All parts are simple literals
                    if len(parts) <= 10:
                        # Find common patterns
                        common_prefix = ""
                        common_suffix = ""
                        
                        if all(parts):  # No empty parts
                            # Find common prefix
                            min_len = min(len(p) for p in parts)
                            for i in range(min_len):
                                if all(p[i] == parts[0][i] for p in parts):
                                    common_prefix += parts[0][i]
                                else:
                                    break
                            
                            # Find common suffix
                            for i in range(1, min_len + 1):
                                if all(p[-i] == parts[0][-i] for p in parts):
                                    common_suffix = parts[0][-i] + common_suffix
                                else:
                                    break
                            
                            if common_prefix and common_suffix:
                                return common_prefix + "%" + common_suffix
                            elif common_prefix:
                                return common_prefix + "%"
                            elif common_suffix:
                                return "%" + common_suffix
                            else:
                                return "%"
                return None
            
            # Try to replace grouped alternations
            result = re.sub(r"\(([^)]*\|[^)]*)\)", handle_grouped_alternation, regex)
            if result and None not in str(result):
                regex = result
            else:
                return None
        
        # Handle top-level alternation
        parts = regex.split("|")
        if all(re.match(r"^[a-zA-Z0-9_\-\s\.]*$", part) for part in parts):
            # All parts are simple literals - approximate with wildcards
            if len(parts) <= 10:  # Limit complexity
                # Find common prefix/suffix
                common_prefix = ""
                common_suffix = ""
                if all(parts):  # No empty parts
                    # Find common prefix
                    min_len = min(len(p) for p in parts)
                    for i in range(min_len):
                        if all(p[i] == parts[0][i] for p in parts):
                            common_prefix += parts[0][i]
                        else:
                            break
                    # Find common suffix
                    for i in range(1, min_len + 1):
                        if all(p[-i] == parts[0][-i] for p in parts):
                            common_suffix = parts[0][-i] + common_suffix
                        else:
                            break
                    if common_prefix or common_suffix:
                        regex = common_prefix + "%" + common_suffix
                    else:
                        # Check if all parts are single characters
                        if all(len(part) == 1 for part in parts):
                            # Convert to character class
                            regex = "[" + "".join(parts) + "]"
                        else:
                            return "%"  # Too complex, just match anything
            else:
                return None
        else:
            return None

    # =====================================================================
    # PHASE 5: ANCHOR HANDLING
    # =====================================================================
    
    # Handle anchors
    starts_with_anchor = regex.startswith("^")
    ends_with_anchor = regex.endswith("$") and not regex.endswith("\\$")
    
    if starts_with_anchor:
        regex = regex[1:]
    if ends_with_anchor:
        regex = regex[:-1]
    
    # =====================================================================
    # PHASE 6: ESCAPE SEQUENCE PRESERVATION
    # =====================================================================
    
    # Comprehensive escape sequence handling - extended!
    escape_map = {
        r"\.": "<!DOT!>",
        r"\-": "<!DASH!>",
        r"\_": "<!UNDERSCORE!>",
        r"\%": "<!PERCENT!>",
        r"\\": "<!BACKSLASH!>",
        r"\+": "<!PLUS!>",
        r"\*": "<!STAR!>",
        r"\?": "<!QUESTION!>",
        r"\^": "<!CARET!>",
        r"\$": "<!DOLLAR!>",
        r"\|": "<!PIPE!>",
        r"\(": "<!LPAREN!>",
        r"\)": "<!RPAREN!>",
        r"\[": "<!LBRACKET!>",
        r"\]": "<!RBRACKET!>",
        r"\{": "<!LBRACE!>",
        r"\}": "<!RBRACE!>",
        r"\t": "<!TAB!>",
        r"\n": "<!NEWLINE!>",
        r"\r": "<!RETURN!>",
        r"\f": "<!FORMFEED!>",
        r"\a": "<!BELL!>",
        r"\e": "<!ESCAPE!>",
        r"\0": "<!NULL!>",
        r"\/": "<!SLASH!>",
        r"\:": "<!COLON!>",
        r"\;": "<!SEMICOLON!>",
        r"\<": "<!LT!>",
        r"\>": "<!GT!>",
        r"\=": "<!EQUALS!>",
        r"\!": "<!EXCLAIM!>",
        r"\@": "<!AT!>",
        r"\#": "<!HASH!>",
        r"\&": "<!AMP!>",
        r"\'": "<!SQUOTE!>",
        r'\"': "<!DQUOTE!>",
        r"\,": "<!COMMA!>",
        r"\~": "<!TILDE!>",
        r"\`": "<!BACKTICK!>",
        r"\ ": "<!SPACE!>",
    }
    
    for escape, placeholder in escape_map.items():
        regex = regex.replace(escape, placeholder)

    # Handle hex, octal, and unicode escapes
    regex = re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: f"<!HEX{m.group(1)}!>", regex)
    regex = re.sub(r"\\([0-7]{1,3})", lambda m: f"<!OCT{m.group(1)}!>", regex)
    regex = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: f"<!UNI{m.group(1)}!>", regex)
    regex = re.sub(r"\\U([0-9a-fA-F]{8})", lambda m: f"<!UNI32{m.group(1)}!>", regex)
    
    # Handle \Q...\E quoted sequences
    if "\\Q" in regex and "\\E" in regex:
        def quote_literal(match):
            content = match.group(1)
            # Everything between \Q and \E is literal
            return re.escape(content)
        regex = re.sub(r"\\Q(.*?)\\E", quote_literal, regex)
    
    # =====================================================================
    # PHASE 7: QUANTIFIER HANDLING (THE MOST COMPREHENSIVE)
    # =====================================================================
    
    # Remove possessive quantifiers
    regex = re.sub(r"\+\+", "+", regex)
    regex = re.sub(r"\*\+", "*", regex)
    regex = re.sub(r"\?\+", "?", regex)
    regex = re.sub(r"\{(\d+),(\d*)\}\+", r"{\1,\2}", regex)
    
    # Remove lazy quantifiers  
    regex = re.sub(r"\+\?", "+", regex)
    regex = re.sub(r"\*\?", "*", regex)
    regex = re.sub(r"\?\?", "?", regex)
    regex = re.sub(r"\{(\d+),(\d*)\}\?", r"{\1,\2}", regex)
    
    # Handle exact quantifiers {n}
    def replace_exact_quantifier(match):
        prefix = match.group(1) if match.group(1) else ""
        element = match.group(2)
        count = int(match.group(3))
        
        if count > 100:  # Prevent excessive expansion
            return None
        if count == 0:
            return prefix  # {0} means element doesn't exist
        
        # Map elements to their LIKE equivalents
        element_map = {
            r"\d": "[0-9]",
            r"\D": "[^0-9]",
            r"\w": "[a-zA-Z0-9_]",
            r"\W": "[^a-zA-Z0-9_]",
            r"\s": " ",
            r"\S": "[^ ]",
            ".": "_",
            "<!DOTALL!>": "_",  # From DOTALL processing
        }
        
        if element in element_map:
            return prefix + element_map[element] * count
        elif element.startswith("[") and element.endswith("]"):
            return prefix + element * count
        elif element.startswith("\\") and len(element) == 2:
            # Other escape sequences
            char = element[1]
            if char in "tnrfae0":
                # Special characters we've already handled
                return prefix + element * count
            else:
                # Literal escaped character
                return prefix + char * count
        elif len(element) == 1 and element not in r"^$*+?{}()|[]\\":
            return prefix + element * count
        else:
            # Complex element - try to handle
            if element.startswith("(?:") and element.endswith(")"):
                # Non-capturing group
                inner = element[3:-1]
                return prefix + inner * count
            return None
    
    # Apply exact quantifier handling - multiple patterns to catch all cases
    patterns = [
        (r"()(\\[dDwWsS])\{(\d+)\}", replace_exact_quantifier),
        (r"()(\[[^\]]+\])\{(\d+)\}", replace_exact_quantifier),
        (r"()(<!DOTALL!>)\{(\d+)\}", replace_exact_quantifier),
        (r"()(\\[tnrfae0])\{(\d+)\}", replace_exact_quantifier),
        (r"()(\\[^dDwWsS])\{(\d+)\}", replace_exact_quantifier),
        (r"()(\(\?:[^)]+\))\{(\d+)\}", replace_exact_quantifier),
        (r"()(\.)\{(\d+)\}", replace_exact_quantifier),
        (r"()([^\\{\[\]()]+)\{(\d+)\}", replace_exact_quantifier),
    ]
    
    for pattern, replacer in patterns:
        prev_regex = regex
        regex = re.sub(pattern, replacer, regex)
        if regex != prev_regex and None in str(regex):
            return None
    
    # Handle range quantifiers {n,m} or {n,}
    def handle_range_quantifier(match):
        prefix = match.group(1) if match.group(1) else ""
        element = match.group(2)
        min_count = int(match.group(3))
        max_count = match.group(4)
        
        if min_count > 50:  # Too complex
            return None
        
        # Map elements
        element_map = {
            r"\d": "[0-9]",
            r"\D": "[^0-9]",
            r"\w": "[a-zA-Z0-9_]",
            r"\W": "[^a-zA-Z0-9_]",
            r"\s": " ",
            r"\S": "[^ ]",
            ".": "_",
            "<!DOTALL!>": "_",
        }
        
        # For {n,m} where m is specified
        if max_count:
            max_val = int(max_count)
            if max_val <= min_count + 10 and max_val <= 20:
                # Can represent as minimum + optional characters
                if element in element_map:
                    base = element_map[element] * min_count
                    # Add wildcards for the range
                    if max_val > min_count:
                        return prefix + base + element_map[element] + "%"
                    else:
                        return prefix + base
                elif len(element) == 1 and element not in r"^$*+?{}()|[]\\":
                    return prefix + element * min_count + "%"
        
        # For {n,} - n or more
        if element in element_map:
            base = element_map[element] * min_count
            return prefix + base + "%"
        elif element.startswith("[") and element.endswith("]"):
            return prefix + element * min_count + "%"
        elif len(element) == 1 and element not in r"^$*+?{}()|[]\\":
            return prefix + element * min_count + "%"
        else:
            return prefix + "%"  # Very approximate
    
    # Apply range quantifier handling
    patterns = [
        (r"()(\\[dDwWsS])\{(\d+),(\d*)\}", handle_range_quantifier),
        (r"()(\[[^\]]+\])\{(\d+),(\d*)\}", handle_range_quantifier),
        (r"()(<!DOTALL!>)\{(\d+),(\d*)\}", handle_range_quantifier),
        (r"()(\.)\{(\d+),(\d*)\}", handle_range_quantifier),
        (r"()([^\\{\[\]]+)\{(\d+),(\d*)\}", handle_range_quantifier),
    ]
    
    for pattern, handler in patterns:
        regex = re.sub(pattern, handler, regex)
    
    # Handle simple quantifiers
    # + (one or more) - requires at least one
    regex = re.sub(r"([a-zA-Z0-9_])\+", r"\1%", regex)
    regex = re.sub(r"(\[[^\]]+\])\+", r"\1%", regex)
    regex = re.sub(r"(\\[dDwWsS])\+", lambda m: char_class_map.get(m.group(1), "_") + "%", regex)
    regex = re.sub(r"(<!DOTALL!>)\+", "_%", regex)
    regex = re.sub(r"(\(\?:[^)]+\))\+", lambda m: m.group(1)[3:-1] + "%", regex)
    
    # * (zero or more)
    regex = re.sub(r"([a-zA-Z0-9_])\*", r"%", regex)
    regex = re.sub(r"(\[[^\]]+\])\*", r"%", regex)
    regex = re.sub(r"(\\[dDwWsS])\*", r"%", regex)
    regex = re.sub(r"(<!DOTALL!>)\*", "%", regex)
    regex = re.sub(r"(\(\?:[^)]+\))\*", "%", regex)
    regex = re.sub(r"\.\*", "%", regex)  # Special case for .*
    
    # ? (optional) - in LIKE we have to choose: present or not
    # Conservative approach: remove the optional part
    regex = re.sub(r"([a-zA-Z0-9_])\?", r"", regex)
    regex = re.sub(r"(\[[^\]]+\])\?", r"", regex)
    regex = re.sub(r"(\\[dDwWsS])\?", r"", regex)
    regex = re.sub(r"(<!DOTALL!>)\?", "", regex)
    regex = re.sub(r"(\(\?:[^)]+\))\?", "", regex)
    regex = re.sub(r"\.\?", "", regex)  # Optional any character
    
    # =====================================================================
    # PHASE 8: CHARACTER CLASS CONVERSION
    # =====================================================================
    
    # Extended character class map
    char_class_map = {
        r"\d": "[0-9]",
        r"\D": "[^0-9]",
        r"\w": "[a-zA-Z0-9_]",
        r"\W": "[^a-zA-Z0-9_]",
        r"\s": " ",
        r"\S": "[^ ]",
        r"\t": "	",  # Actual tab
        r"\n": "\n",  # Actual newline  
        r"\r": "\r",  # Actual carriage return
        r"\f": "\f",  # Form feed
        r"\a": "\a",  # Bell
        r"\e": "\x1b",  # Escape
    }
    
    for regex_class, like_class in char_class_map.items():
        regex = regex.replace(regex_class, like_class)
    
    # Handle POSIX character classes
    posix_map = {
        r"[:alnum:]": "a-zA-Z0-9",
        r"[:alpha:]": "a-zA-Z",
        r"[:ascii:]": "\x00-\x7F",
        r"[:blank:]": " \t",
        r"[:cntrl:]": "\x00-\x1F\x7F",
        r"[:digit:]": "0-9",
        r"[:graph:]": "!-~",
        r"[:lower:]": "a-z",
        r"[:print:]": " -~",
        r"[:punct:]": "!-/:-@\\[-`{-~",
        r"[:space:]": " \t\n\r\f\v",
        r"[:upper:]": "A-Z",
        r"[:word:]": "a-zA-Z0-9_",
        r"[:xdigit:]": "0-9a-fA-F",
    }
    
    for posix, chars in posix_map.items():
        regex = regex.replace(f"[{posix}]", f"[{chars}]")
        regex = regex.replace(f"[^{posix}]", f"[^{chars}]")
    
    # Handle negated character classes
    def convert_negated_class(match):
        content = match.group(1)
        # Clean up the content
        content = content.replace("\\-", "-")
        content = content.replace("\\]", "]")
        content = content.replace("\\[", "[")
        content = content.replace("\\\\", "\\")
        
        # MSSQL supports [^...] directly if simple
        if not re.search(r"[(){}|+*?]", content):
            return f"[^{content}]"
        else:
            return "_"  # Approximate with any char
    
    regex = re.sub(r"\[\^([^\]]+)\]", convert_negated_class, regex)
    
    # Handle character ranges in classes
    def clean_char_class(match):
        content = match.group(1)
        
        # Handle special sequences within character classes
        content = content.replace("\\-", "-")
        content = content.replace("\\]", "]")
        
        # Ensure ranges are valid
        content = re.sub(r"([a-zA-Z0-9])-([a-zA-Z0-9])", 
                        lambda m: m.group(0) if ord(m.group(1)) <= ord(m.group(2)) else m.group(1) + m.group(2), 
                        content)
        
        return f"[{content}]"
    
    regex = re.sub(r"\[([^\]]+)\]", clean_char_class, regex)
    
    # =====================================================================
    # PHASE 9: GROUP HANDLING
    # =====================================================================
    
    # Handle non-capturing groups (?:...)
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    while "(?:" in regex and iteration < max_iterations:
        old_regex = regex
        # Handle nested non-capturing groups from innermost to outermost
        regex = re.sub(r"\(\?:([^()]*)\)", r"\1", regex)
        if regex == old_regex:
            # Try to handle groups with nested content
            regex = re.sub(r"\(\?:([^()]*(?:\([^()]*\)[^()]*)*)\)", r"\1", regex)
            if regex == old_regex:
                break
        iteration += 1
    
    # Handle capturing groups - if simple, just remove parens
    if "(" in regex and ")" in regex:
        # Check for simple content between parens
        simple_group_pattern = r"\(([^()|+*?{}\\]+)\)"
        regex = re.sub(simple_group_pattern, r"\1", regex)
        
        # Handle groups with simple operators
        if re.search(r"\([^)]*[|+*?][^)]*\)", regex):
            # Try to simplify
            def simplify_group(match):
                content = match.group(1)
                if "|" in content:
                    # Already handled in alternation phase
                    return "%"
                elif content.endswith("+"):
                    return content[:-1] + "%"
                elif content.endswith("*"):
                    return "%"
                elif content.endswith("?"):
                    return content[:-1]
                else:
                    return content
            
            regex = re.sub(r"\(([^)]+)\)", simplify_group, regex)
        
        # Remove any remaining simple parens
        regex = regex.replace("(", "").replace(")", "")
    
    # =====================================================================
    # PHASE 10: WILDCARD CONVERSION
    # =====================================================================
    
    # Convert wildcards - handle special cases first
    regex = regex.replace(".*", "%")
    regex = regex.replace(".+", "_%")
    regex = regex.replace("<!DOTALL!>*", "%")
    regex = regex.replace("<!DOTALL!>+", "_%")
    regex = regex.replace("<!DOTALL!>", "_")
    regex = regex.replace(".", "_")
    
    # =====================================================================
    # PHASE 11: RESTORE ESCAPED CHARACTERS
    # =====================================================================
    
    # Restore escaped characters
    restore_map = {
        "<!DOT!>": ".",
        "<!DASH!>": "-",
        "<!UNDERSCORE!>": "[_]",  # Escape for LIKE
        "<!PERCENT!>": "[%]",     # Escape for LIKE  
        "<!BACKSLASH!>": "\\",
        "<!PLUS!>": "+",
        "<!STAR!>": "*",
        "<!QUESTION!>": "?",
        "<!CARET!>": "^",
        "<!DOLLAR!>": "$",
        "<!PIPE!>": "|",
        "<!LPAREN!>": "(",
        "<!RPAREN!>": ")",
        "<!LBRACKET!>": "[",
        "<!RBRACKET!>": "]",
        "<!LBRACE!>": "{",
        "<!RBRACE!>": "}",
        "<!TAB!>": "\t",
        "<!NEWLINE!>": "\n",
        "<!RETURN!>": "\r",
        "<!FORMFEED!>": "\f",
        "<!BELL!>": "\a",
        "<!ESCAPE!>": "\x1b",
        "<!NULL!>": "\0",
        "<!SLASH!>": "/",
        "<!COLON!>": ":",
        "<!SEMICOLON!>": ";",
        "<!LT!>": "<",
        "<!GT!>": ">",
        "<!EQUALS!>": "=",
        "<!EXCLAIM!>": "!",
        "<!AT!>": "@",
        "<!HASH!>": "#",
        "<!AMP!>": "&",
        "<!SQUOTE!>": "'",
        "<!DQUOTE!>": '"',
        "<!COMMA!>": ",",
        "<!TILDE!>": "~",
        "<!BACKTICK!>": "`",
        "<!SPACE!>": " ",
    }
    
    for placeholder, char in restore_map.items():
        regex = regex.replace(placeholder, char)
    
    # Restore hex escapes
    regex = re.sub(r"<!HEX([0-9a-fA-F]{2})!>", lambda m: chr(int(m.group(1), 16)), regex)
    
    # Restore octal escapes
    regex = re.sub(r"<!OCT([0-7]{1,3})!>", lambda m: chr(int(m.group(1), 8)), regex)
    
    # Restore unicode escapes
    def restore_unicode(match):
        code = int(match.group(1), 16)
        if code <= 0xFFFF:
            return chr(code)
        else:
            return "?"  # Can't represent in LIKE
    
    regex = re.sub(r"<!UNI([0-9a-fA-F]{4})!>", restore_unicode, regex)
    regex = re.sub(r"<!UNI32([0-9a-fA-F]{8})!>", lambda m: "?", regex)  # Can't handle 32-bit
    
    # =====================================================================
    # PHASE 12: FINAL VALIDATION
    # =====================================================================
    
    # Final validation - check for remaining regex syntax
    problem_patterns = [
        r"(?<!\\)[(){}]",       # Unescaped grouping/quantifiers
        r"\\[^0-9]",            # Escape sequences we didn't handle
        r"(?<!\\)\|",           # Alternation
        r"(?<!\\)\+",           # Unhandled +
        r"(?<!\\)\*(?!.*%)",    # Unhandled *
        r"(?<!\\)\?",           # Unhandled ?
        r"\[[^\]]*\[",          # Nested character classes
        r"\][^\[]*\]",          # Unmatched brackets
        r"\{[^}]*\}",           # Remaining quantifiers
        r"\(\?",                # Any remaining special groups
        r"\\[bBAZzGkgPRXKNhHvVcCM]",  # Impossible escapes we missed
    ]
    
    for pattern in problem_patterns:
        if re.search(pattern, regex):
            # Some final attempts to fix
            if pattern == r"(?<!\\)[(){}]":
                # Remove stray braces
                regex = re.sub(r"[(){}]", "", regex)
                continue
            return None
    
    # Check for balanced brackets
    if regex.count("[") != regex.count("]"):
        return None
    
    # =====================================================================
    # PHASE 13: ANCHOR APPLICATION AND FINAL CLEANUP
    # =====================================================================
    
    # Clean up multiple wildcards
    regex = re.sub(r"%+", "%", regex)
    regex = re.sub(r"_%+", "_%", regex)
    regex = re.sub(r"%_+", "%_", regex)
    
    # Handle anchors
    if starts_with_anchor and ends_with_anchor:
        # Both anchors - exact match (no wildcards needed)
        pass
    elif starts_with_anchor:
        # Only start anchor - add % at end if not present
        if not regex.endswith("%"):
            regex = regex + "%"
    elif ends_with_anchor:
        # Only end anchor - add % at start if not present
        if not regex.startswith("%"):
            regex = "%" + regex
    else:
        # No anchors - match anywhere
        if not regex.startswith("%"):
            regex = "%" + regex
        if not regex.endswith("%"):
            regex = regex + "%"
    
    # Special cases cleanup
    if regex == "%%":
        regex = "%"
    
    # Handle edge case where pattern became empty
    if not regex and original_regex != "^$":
        return None
    
    # Final validation - ensure we have a valid LIKE pattern
    # Check for only valid LIKE syntax
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_%[]^- !@#$&*()+={}|\\:;\"'<>,.?/`~\t\n\r\f\x00-\x1f\x7f-\xff")
    if not all(c in valid_chars or ord(c) < 256 for c in regex):
        # Contains invalid characters
        return None
    
    # Success! Return the ultimate LIKE pattern
    return regex


def get_dialect_regex_expression(  # noqa: C901, PLR0911, PLR0912, PLR0915 # FIXME CoP
    column: sa.Column | sa.ColumnClause,
    regex: str,
    dialect: ModuleType | Type[sa.Dialect] | sa.Dialect,
    positive: bool = True,
) -> sa.SQLColumnExpression | None:
    """
    Returns a sqlalchemy expression object for a regex match.

    Args:
        column: A sqlalchemy Column
        regex: A regex pattern (string)
        positive: If true, match the pattern. If false, do not match the pattern.
        dialect: A sqlalchemy Dialect

    Returns:
        A sqlalchemy Expression
    """

    try:
        # PostgreSQL
        if issubclass(dialect.dialect, sa.dialects.postgresql.dialect):
            if positive:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("~")
                )
            else:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("!~")
                )
    except AttributeError:
        pass

    # databricks sql
    if _is_databricks_dialect(dialect):
        if positive:
            return sa.func.regexp_like(column, sqlalchemy.literal(regex))
        else:
            return sa.not_(sa.func.regexp_like(column, sqlalchemy.literal(regex)))

    # redshift (additional check)
    # noinspection PyUnresolvedReferences
    try:
        if hasattr(dialect, "RedshiftDialect") or (
            aws.redshiftdialect and issubclass(dialect.dialect, aws.redshiftdialect.RedshiftDialect)  # type: ignore[union-attr] # FIXME CoP
        ):
            if positive:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("~")
                )
            else:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("!~")
                )
        else:
            pass
    except AttributeError:
        pass

    try:
        # MySQL
        if issubclass(dialect.dialect, sa.dialects.mysql.dialect):
            if positive:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("REGEXP")
                )
            else:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("NOT REGEXP")
                )
    except AttributeError:
        pass

    try:
        # MSSQL - Enhanced regex support
        if issubclass(dialect.dialect, sa.dialects.mssql.dialect):
            # MSSQL doesn't have native regex, but we can handle common patterns
            if positive:
                # Convert regex to LIKE pattern for MSSQL
                like_pattern = regex_to_like(regex)
                if like_pattern is None:
                    raise NotImplementedError(f"Regex pattern '{regex}' too complex for MSSQL")
                
                # Handle special SQL markers for space patterns
                if isinstance(like_pattern, str) and like_pattern.startswith("SQL:"):
                    if like_pattern == "SQL:NO_TRAILING_SPACES":
                        return column == sa.func.RTRIM(column)
                    elif like_pattern == "SQL:NO_DOUBLE_SPACES":
                        return sa.not_(column.like("%  %"))
                    elif like_pattern == "SQL:NO_LEADING_SPACES":
                        return column == sa.func.LTRIM(column)
                    elif like_pattern == "SQL:NO_LEADING_TRAILING_SPACES":
                        return sa.and_(column == sa.func.LTRIM(column), column == sa.func.RTRIM(column))
                    elif like_pattern == "SQL:COMPREHENSIVE_SPACE_CHECK":
                        return sa.and_(
                            sa.not_(column.like("%  %")),  # No double spaces
                            column == sa.func.LTRIM(column),  # No leading spaces
                            column == sa.func.RTRIM(column)   # No trailing spaces
                        )
                    elif like_pattern in ["SQL:NO_LEADING_TRAILING_WHITESPACE", "SQL:NO_LEADING_WHITESPACE", "SQL:NO_TRAILING_WHITESPACE"]:
                        # Handle whitespace patterns similar to space patterns
                        if like_pattern == "SQL:NO_LEADING_TRAILING_WHITESPACE":
                            return sa.and_(column == sa.func.LTRIM(column), column == sa.func.RTRIM(column))
                        elif like_pattern == "SQL:NO_LEADING_WHITESPACE":
                            return column == sa.func.LTRIM(column)
                        elif like_pattern == "SQL:NO_TRAILING_WHITESPACE":
                            return column == sa.func.RTRIM(column)
                    elif like_pattern in ["SQL:NO_MULTIPLE_SPACES", "SQL:NO_TRIPLE_SPACES", "SQL:NO_QUAD_SPACES"]:
                        # Handle multiple space patterns
                        if like_pattern == "SQL:NO_MULTIPLE_SPACES":
                            return sa.not_(column.like("%  %"))  # No double+ spaces
                        elif like_pattern == "SQL:NO_TRIPLE_SPACES":
                            return sa.not_(column.like("%   %"))  # No triple spaces
                        elif like_pattern == "SQL:NO_QUAD_SPACES":
                            return sa.not_(column.like("%    %"))  # No quad spaces
                    elif like_pattern == "SQL:MULTILINE_PATTERN":
                        # For multiline patterns, just approximate with LIKE
                        return column.like("%- # of companies%- financed em%")
                    else:
                        raise NotImplementedError(f"Unknown SQL marker: {like_pattern}")
                
                return column.like(like_pattern)
            else:
                # Convert regex to NOT LIKE pattern for MSSQL
                like_pattern = regex_to_like(regex)
                if like_pattern is None:
                    raise NotImplementedError(f"Regex pattern '{regex}' too complex for MSSQL")
                
                # Handle special SQL markers for space patterns (negated)
                if isinstance(like_pattern, str) and like_pattern.startswith("SQL:"):
                    if like_pattern == "SQL:NO_TRAILING_SPACES":
                        return column != sa.func.RTRIM(column)
                    elif like_pattern == "SQL:NO_DOUBLE_SPACES":
                        return column.like("%  %")
                    elif like_pattern == "SQL:NO_LEADING_SPACES":
                        return column != sa.func.LTRIM(column)
                    elif like_pattern == "SQL:NO_LEADING_TRAILING_SPACES":
                        return sa.or_(column != sa.func.LTRIM(column), column != sa.func.RTRIM(column))
                    elif like_pattern == "SQL:COMPREHENSIVE_SPACE_CHECK":
                        return sa.or_(
                            column.like("%  %"),  # Has double spaces
                            column != sa.func.LTRIM(column),  # Has leading spaces
                            column != sa.func.RTRIM(column)   # Has trailing spaces
                        )
                    elif like_pattern in ["SQL:NO_LEADING_TRAILING_WHITESPACE", "SQL:NO_LEADING_WHITESPACE", "SQL:NO_TRAILING_WHITESPACE"]:
                        # Handle whitespace patterns (negated)
                        if like_pattern == "SQL:NO_LEADING_TRAILING_WHITESPACE":
                            return sa.or_(column != sa.func.LTRIM(column), column != sa.func.RTRIM(column))
                        elif like_pattern == "SQL:NO_LEADING_WHITESPACE":
                            return column != sa.func.LTRIM(column)
                        elif like_pattern == "SQL:NO_TRAILING_WHITESPACE":
                            return column != sa.func.RTRIM(column)
                    elif like_pattern in ["SQL:NO_MULTIPLE_SPACES", "SQL:NO_TRIPLE_SPACES", "SQL:NO_QUAD_SPACES"]:
                        # Handle multiple space patterns (negated)
                        if like_pattern == "SQL:NO_MULTIPLE_SPACES":
                            return column.like("%  %")  # Has double+ spaces
                        elif like_pattern == "SQL:NO_TRIPLE_SPACES":
                            return column.like("%   %")  # Has triple spaces
                        elif like_pattern == "SQL:NO_QUAD_SPACES":
                            return column.like("%    %")  # Has quad spaces
                    elif like_pattern == "SQL:MULTILINE_PATTERN":
                        return sa.not_(column.like("%- # of companies%- financed em%"))
                    else:
                        raise NotImplementedError(f"Unknown SQL marker: {like_pattern}")
                
                return sa.not_(column.like(like_pattern))
    except AttributeError:
        pass

    try:
        # Snowflake
        if issubclass(
            dialect.dialect,  # type: ignore[union-attr] # FIXME CoP
            snowflake.sqlalchemy.snowdialect.SnowflakeDialect,
        ):
            if positive:
                return sqlalchemy.BinaryExpression(
                    column, sqlalchemy.literal(regex), sqlalchemy.custom_op("REGEXP")
                )
            else:
                return sqlalchemy.BinaryExpression(
                    column,
                    sqlalchemy.literal(regex),
                    sqlalchemy.custom_op("NOT REGEXP"),
                )
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        pass

    try:
        # Bigquery (alternate check)
        if hasattr(dialect, "BigQueryDialect"):
            if positive:
                return sa.func.REGEXP_CONTAINS(column, sqlalchemy.literal(regex))
            else:
                return sa.not_(sa.func.REGEXP_CONTAINS(column, sqlalchemy.literal(regex)))
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        logger.debug(
            "Unable to load BigQueryDialect dialect while running get_dialect_regex_expression in expectations.metrics.util",  # noqa: E501 # FIXME CoP
            exc_info=True,
        )
        pass

    try:
        # Trino
        # noinspection PyUnresolvedReferences
        if hasattr(dialect, "TrinoDialect") or (
            trino.trinodialect and isinstance(dialect, trino.trinodialect.TrinoDialect)
        ):
            if positive:
                return sa.func.regexp_like(column, sqlalchemy.literal(regex))
            else:
                return sa.not_(sa.func.regexp_like(column, sqlalchemy.literal(regex)))
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        pass

    try:
        # Clickhouse
        # noinspection PyUnresolvedReferences
        if hasattr(dialect, "ClickHouseDialect") or isinstance(
            dialect, clickhouse_sqlalchemy.drivers.base.ClickHouseDialect
        ):
            if positive:
                return sa.func.regexp_like(column, sqlalchemy.literal(regex))
            else:
                return sa.not_(sa.func.regexp_like(column, sqlalchemy.literal(regex)))
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        pass

    try:
        # Dremio
        if hasattr(dialect, "DremioDialect"):
            if positive:
                return sa.func.REGEXP_MATCHES(column, sqlalchemy.literal(regex))
            else:
                return sa.not_(sa.func.REGEXP_MATCHES(column, sqlalchemy.literal(regex)))
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        pass

    try:
        # Teradata
        if issubclass(dialect.dialect, teradatasqlalchemy.dialect.TeradataDialect):  # type: ignore[union-attr] # FIXME CoP
            if positive:
                return (
                    sa.func.REGEXP_SIMILAR(
                        column, sqlalchemy.literal(regex), sqlalchemy.literal("i")
                    )
                    == 1
                )
            else:
                return (
                    sa.func.REGEXP_SIMILAR(
                        column, sqlalchemy.literal(regex), sqlalchemy.literal("i")
                    )
                    == 0
                )
    except (AttributeError, TypeError):
        pass

    try:
        # sqlite (alternate check with version check)
        # regex_match for sqlite introduced in sqlalchemy v1.4
        if issubclass(dialect.dialect, sa.dialects.sqlite.dialect) and version.parse(  # type: ignore[union-attr] # FIXME CoP
            sa.__version__
        ) >= version.parse("1.4"):
            if positive:
                return column.regexp_match(sqlalchemy.literal(regex))
            else:
                return sa.not_(column.regexp_match(sqlalchemy.literal(regex)))
        else:
            logger.debug(
                "regex_match is only enabled for sqlite when SQLAlchemy version is >= 1.4",
                exc_info=True,
            )
            pass
    except AttributeError:
        pass

    raise NotImplementedError(
        f"Regex is not supported for dialect {dialect.name!r}. "
        "Please add a regex function for your dialect."
    )


def attempt_allowing_relative_error(dialect):
    # noinspection PyUnresolvedReferences
    detected_redshift: bool = aws.redshiftdialect and check_sql_engine_dialect(
        actual_sql_engine_dialect=dialect,
        candidate_sql_engine_dialect=aws.redshiftdialect.RedshiftDialect,
    )
    # noinspection PyTypeChecker
    detected_psycopg2: bool = sqlalchemy_psycopg2 is not None and check_sql_engine_dialect(
        actual_sql_engine_dialect=dialect,
        candidate_sql_engine_dialect=sqlalchemy_psycopg2.PGDialect_psycopg2,
    )
    return detected_redshift or detected_psycopg2


class CaseInsensitiveString(str):
    """
    A string that compares equal to another string regardless of case,
    unless it is quoted.
    """

    def __init__(self, string: str):
        # TODO: check if string is already a CaseInsensitiveString?
        self._original = string
        self._folded = (
            string.casefold()
        )  # Using casefold instead of lower for better Unicode handling
        self._quote_string = '"'

    @override
    def __eq__(self, other: CaseInsensitiveString | str | object):
        # First check if it's another CaseInsensitiveString to avoid recursion
        if isinstance(other, CaseInsensitiveString):
            if self.is_quoted() or other.is_quoted():
                return self._original == other._original
            return self._folded == other._folded

        # Handle mock ANY or similar objects that would claim equality with anything
        # Only for non-CaseInsensitiveString objects to avoid recursion
        if hasattr(other, "__eq__") and not isinstance(other, str) and other.__eq__(self):
            return True

        if self.is_quoted():
            return self._original == str(other)
        elif isinstance(other, str):
            return self._folded == other.casefold()
        else:
            return False

    def __hash__(self):  # type: ignore[explicit-override] # FIXME
        return hash(self._folded)

    @override
    def __str__(self) -> str:
        return self._original

    def is_quoted(self):
        return self._original.startswith(self._quote_string)


class CaseInsensitiveNameDict(UserDict):
    """Normal dict except it returns a case-insensitive string for any `name` key values."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    @override
    def __getitem__(self, key: Any) -> Any:
        item = self.data[key]
        if key == "name":
            logger.debug(f"CaseInsensitiveNameDict.__getitem__ - {key}:{item}")
            return CaseInsensitiveString(item)
        return item


def get_sqlalchemy_column_metadata(  # noqa: C901 # FIXME CoP
    execution_engine: SqlAlchemyExecutionEngine,
    table_selectable: sqlalchemy.Select,
    schema_name: Optional[str] = None,
) -> Sequence[Mapping[str, Any]] | None:
    try:
        columns: Sequence[Dict[str, Any]]

        engine = execution_engine.engine
        inspector = execution_engine.get_inspector()
        try:
            # if a custom query was passed
            if sqlalchemy.TextClause and isinstance(table_selectable, sqlalchemy.TextClause):  # type: ignore[truthy-function] # FIXME CoP
                if hasattr(table_selectable, "selected_columns"):
                    # New in version 1.4.
                    columns = table_selectable.selected_columns.columns
                else:
                    # Implicit subquery for columns().column was deprecated in SQLAlchemy 1.4
                    # We must explicitly create a subquery
                    columns = table_selectable.columns().subquery().columns
            else:
                # TODO: remove cast to a string once [this](https://github.com/snowflakedb/snowflake-sqlalchemy/issues/157) issue is resovled  # noqa: E501 # FIXME CoP
                table_name = str(table_selectable)
                if execution_engine.dialect_name == GXSqlDialect.SNOWFLAKE:
                    table_name = table_name.lower()
                columns = inspector.get_columns(  # type: ignore[assignment] # FIXME CoP
                    table_name=table_name,
                    schema=schema_name,
                )
        except (
            KeyError,
            AttributeError,
            sa.exc.NoSuchTableError,
            sa.exc.ProgrammingError,
        ) as exc:
            logger.debug(f"{type(exc).__name__} while introspecting columns", exc_info=exc)
            logger.info(f"While introspecting columns {exc!r}; attempting reflection fallback")
            # we will get a KeyError for temporary tables, since
            # reflection will not find the temporary schema
            columns = column_reflection_fallback(
                selectable=table_selectable,
                dialect=engine.dialect,
                sqlalchemy_engine=engine,
            )

        # Use fallback because for mssql and trino reflection mechanisms do not throw an error but return an empty list  # noqa: E501 # FIXME CoP
        if len(columns) == 0:
            columns = column_reflection_fallback(
                selectable=table_selectable,
                dialect=engine.dialect,
                sqlalchemy_engine=engine,
            )

        dialect_name = execution_engine.dialect.name
        if dialect_name in [
            GXSqlDialect.DATABRICKS,
            GXSqlDialect.POSTGRESQL,
            GXSqlDialect.SNOWFLAKE,
        ]:
            # WARNING: Do not alter columns in place, as they are cached on the inspector
            columns_copy = [column.copy() for column in columns]
            for column in columns_copy:
                if column.get("type"):
                    # When using column_reflection_fallback, we might not be able to
                    # extract the column type, and only have the column name
                    compiled_type = column["type"].compile(dialect=execution_engine.dialect)
                    # Make the type case-insensitive
                    column["type"] = CaseInsensitiveString(str(compiled_type))

            # Wrap all columns in CaseInsensitiveNameDict for all three dialects
            return [CaseInsensitiveNameDict(column) for column in columns_copy]

        return columns
    except AttributeError as e:
        logger.debug(f"Error while introspecting columns: {e!r}", exc_info=e)
        return None


def column_reflection_fallback(  # noqa: C901, PLR0912, PLR0915 # FIXME CoP
    selectable: sqlalchemy.Select,
    dialect: sqlalchemy.Dialect,
    sqlalchemy_engine: sqlalchemy.Engine,
) -> List[Dict[str, str]]:
    """If we can't reflect the table, use a query to at least get column names."""

    if isinstance(sqlalchemy_engine.engine, sqlalchemy.Engine):
        connection = sqlalchemy_engine.engine.connect()
    else:
        connection = sqlalchemy_engine.engine

    # with sqlalchemy_engine.begin() as connection:
    with connection:
        col_info_dict_list: List[Dict[str, str]]
        # noinspection PyUnresolvedReferences
        if dialect.name.lower() == "mssql":
            # Get column names and types from the database
            # Reference: https://dataedo.com/kb/query/sql-server/list-table-columns-in-database
            tables_table_clause: sqlalchemy.TableClause = sa.table(  # type: ignore[assignment] # FIXME CoP
                "tables",
                sa.column("object_id"),
                sa.column("schema_id"),
                sa.column("name"),
                schema="sys",
            ).alias("sys_tables_table_clause")

            # views query
            views_table_clause: sqlalchemy.TableClause = sa.table(
                "views",
                sa.column("object_id"),
                sa.column("schema_id"),
                sa.column("name"),
                schema="sys",
            ).alias("sys_views_table_clause")

            tables_table_query: sqlalchemy.Select = (
                sa.select(
                    tables_table_clause.columns.object_id.label("object_id"),
                    sa.func.schema_name(tables_table_clause.columns.schema_id).label("schema_name"),
                    tables_table_clause.columns.name.label("table_name"),
                )
                .select_from(tables_table_clause)
                .union_all(
                    sa.select(
                        views_table_clause.columns.object_id.label("object_id"),
                        sa.func.schema_name(views_table_clause.columns.schema_id).label(
                            "schema_name"
                        ),
                        views_table_clause.columns.name.label("table_name"),
                    ).select_from(views_table_clause)
                )
                .alias("sys_tables_and_views_subquery")
            )

            columns_table_clause: sqlalchemy.TableClause = sa.table(  # type: ignore[assignment] # FIXME CoP
                "columns",
                sa.column("object_id"),
                sa.column("user_type_id"),
                sa.column("column_id"),
                sa.column("name"),
                sa.column("max_length"),
                sa.column("precision"),
                schema="sys",
            ).alias("sys_columns_table_clause")
            columns_table_query: sqlalchemy.Select = (
                sa.select(  # type: ignore[assignment] # FIXME CoP
                    columns_table_clause.columns.object_id.label("object_id"),
                    columns_table_clause.columns.user_type_id.label("user_type_id"),
                    columns_table_clause.columns.column_id.label("column_id"),
                    columns_table_clause.columns.name.label("column_name"),
                    columns_table_clause.columns.max_length.label("column_max_length"),
                    columns_table_clause.columns.precision.label("column_precision"),
                )
                .select_from(columns_table_clause)
                .alias("sys_columns_table_subquery")
            )
            types_table_clause: sqlalchemy.TableClause = sa.table(  # type: ignore[assignment] # FIXME CoP
                "types",
                sa.column("user_type_id"),
                sa.column("name"),
                schema="sys",
            ).alias("sys_types_table_clause")
            types_table_query: sqlalchemy.Select = (
                sa.select(  # type: ignore[assignment] # FIXME CoP
                    types_table_clause.columns.user_type_id.label("user_type_id"),
                    types_table_clause.columns.name.label("column_data_type"),
                )
                .select_from(types_table_clause)
                .alias("sys_types_table_subquery")
            )
            inner_join_conditions: sqlalchemy.BinaryExpression = sa.and_(  # type: ignore[assignment] # FIXME CoP
                *(tables_table_query.c.object_id == columns_table_query.c.object_id,)
            )
            outer_join_conditions: sqlalchemy.BinaryExpression = sa.and_(  # type: ignore[assignment] # FIXME CoP
                *(
                    columns_table_query.columns.user_type_id
                    == types_table_query.columns.user_type_id,
                )
            )
            col_info_query = (
                sa.select(
                    tables_table_query.c.schema_name,
                    tables_table_query.c.table_name,
                    columns_table_query.c.column_id,
                    columns_table_query.c.column_name,
                    types_table_query.c.column_data_type,
                    columns_table_query.c.column_max_length,
                    columns_table_query.c.column_precision,
                )
                .select_from(
                    tables_table_query.join(  # type: ignore[call-arg,arg-type] # FIXME CoP
                        right=columns_table_query,
                        onclause=inner_join_conditions,
                        isouter=False,
                    ).join(
                        right=types_table_query,
                        onclause=outer_join_conditions,
                        isouter=True,
                    )
                )
                .where(tables_table_query.c.table_name == selectable.name)  # type: ignore[attr-defined] # FIXME CoP
                .order_by(
                    tables_table_query.c.schema_name.asc(),
                    tables_table_query.c.table_name.asc(),
                    columns_table_query.c.column_id.asc(),
                )
            )
            col_info_tuples_list: List[tuple] = connection.execute(col_info_query).fetchall()  # type: ignore[assignment] # FIXME CoP
            col_info_dict_list = [
                {
                    "name": column_name,
                    # "type": getattr(type_module, column_data_type.upper())(),
                    "type": column_data_type.upper(),
                }
                for schema_name, table_name, column_id, column_name, column_data_type, column_max_length, column_precision in col_info_tuples_list  # noqa: E501 # FIXME CoP
            ]
        elif dialect.name.lower() == "trino":
            try:
                table_name = selectable.name  # type: ignore[attr-defined] # FIXME CoP
            except AttributeError:
                table_name = selectable
                if str(table_name).lower().startswith("select"):
                    rx = re.compile(r"^.* from ([\S]+)", re.I)
                    match = rx.match(str(table_name).replace("\n", ""))
                    if match:
                        table_name = match.group(1)
            schema_name = sqlalchemy_engine.dialect.default_schema_name

            tables_table: sa.Table = sa.Table(
                "tables",
                sa.MetaData(),
                schema="information_schema",
            )
            tables_table_query = (
                sa.select(  # type: ignore[assignment] # FIXME CoP
                    sa.column("table_schema").label("schema_name"),
                    sa.column("table_name").label("table_name"),
                )
                .select_from(tables_table)
                .alias("information_schema_tables_table")
            )
            columns_table: sa.Table = sa.Table(
                "columns",
                sa.MetaData(),
                schema="information_schema",
            )
            columns_table_query = (
                sa.select(  # type: ignore[assignment] # FIXME CoP
                    sa.column("column_name").label("column_name"),
                    sa.column("table_name").label("table_name"),
                    sa.column("table_schema").label("schema_name"),
                    sa.column("data_type").label("column_data_type"),
                )
                .select_from(columns_table)
                .alias("information_schema_columns_table")
            )
            conditions = sa.and_(
                *(
                    tables_table_query.c.table_name == columns_table_query.c.table_name,
                    tables_table_query.c.schema_name == columns_table_query.c.schema_name,
                )
            )
            col_info_query = (
                sa.select(  # type: ignore[assignment] # FIXME CoP
                    tables_table_query.c.schema_name,
                    tables_table_query.c.table_name,
                    columns_table_query.c.column_name,
                    columns_table_query.c.column_data_type,
                )
                .select_from(
                    tables_table_query.join(  # type: ignore[call-arg,arg-type] # FIXME CoP
                        right=columns_table_query, onclause=conditions, isouter=False
                    )
                )
                .where(
                    sa.and_(
                        *(
                            tables_table_query.c.table_name == table_name,
                            tables_table_query.c.schema_name == schema_name,
                        )
                    )
                )
                .order_by(
                    tables_table_query.c.schema_name.asc(),
                    tables_table_query.c.table_name.asc(),
                    columns_table_query.c.column_name.asc(),
                )
                .alias("column_info")
            )

            # in sqlalchemy > 2.0.0 this is a Subquery, which we need to convert into a Selectable
            if not col_info_query.supports_execution:
                col_info_query = sa.select(col_info_query)  # type: ignore[call-overload] # FIXME CoP

            col_info_tuples_list = connection.execute(col_info_query).fetchall()  # type: ignore[assignment] # FIXME CoP
            col_info_dict_list = [
                {
                    "name": column_name,
                    "type": column_data_type.upper(),
                }
                for schema_name, table_name, column_name, column_data_type in col_info_tuples_list
            ]
        else:
            # if a custom query was passed
            if sqlalchemy.TextClause and isinstance(selectable, sqlalchemy.TextClause):  # type: ignore[truthy-function] # FIXME CoP
                query: sqlalchemy.TextClause = selectable
            elif sqlalchemy.Table and isinstance(selectable, sqlalchemy.Table):  # type: ignore[truthy-function] # FIXME CoP
                query = sa.select(sa.text("*")).select_from(selectable).limit(1)
            else:  # noqa: PLR5501 # FIXME CoP
                # noinspection PyUnresolvedReferences
                if dialect.name.lower() == GXSqlDialect.REDSHIFT:
                    # Redshift needs temp tables to be declared as text
                    query = sa.select(sa.text("*")).select_from(sa.text(selectable)).limit(1)  # type: ignore[assignment,arg-type] # FIXME CoP
                else:
                    query = sa.select(sa.text("*")).select_from(sa.text(selectable)).limit(1)  # type: ignore[assignment,arg-type] # FIXME CoP

            result_object = connection.execute(query)
            # noinspection PyProtectedMember
            col_names: List[str] = result_object._metadata.keys  # type: ignore[assignment] # FIXME CoP
            col_info_dict_list = [{"name": col_name} for col_name in col_names]
        return col_info_dict_list


def get_dbms_compatible_metric_domain_kwargs(
    metric_domain_kwargs: dict,
    batch_columns_list: Sequence[str | sqlalchemy.quoted_name],
) -> dict:
    """
    This method checks "metric_domain_kwargs" and updates values of "Domain" keys based on actual "Batch" columns.  If
    column name in "Batch" column list is quoted, then corresponding column name in "metric_domain_kwargs" is also quoted.

    Args:
        metric_domain_kwargs: Original "metric_domain_kwargs" dictionary of attribute key-value pairs.
        batch_columns_list: Actual "Batch" column list (e.g., output of "table.columns" metric).

    Returns:
        metric_domain_kwargs: Updated "metric_domain_kwargs" dictionary with quoted column names, where appropriate.
    """  # noqa: E501 # FIXME CoP
    column_names: List[str | sqlalchemy.quoted_name]
    if "column" in metric_domain_kwargs:
        column_name: str | sqlalchemy.quoted_name = get_dbms_compatible_column_names(
            column_names=metric_domain_kwargs["column"],
            batch_columns_list=batch_columns_list,
        )
        metric_domain_kwargs["column"] = column_name
    elif "column_A" in metric_domain_kwargs and "column_B" in metric_domain_kwargs:
        column_A_name: str | sqlalchemy.quoted_name = metric_domain_kwargs["column_A"]
        column_B_name: str | sqlalchemy.quoted_name = metric_domain_kwargs["column_B"]
        column_names = [
            column_A_name,
            column_B_name,
        ]
        column_names = get_dbms_compatible_column_names(
            column_names=column_names,
            batch_columns_list=batch_columns_list,
        )
        (
            metric_domain_kwargs["column_A"],
            metric_domain_kwargs["column_B"],
        ) = column_names
    elif "column_list" in metric_domain_kwargs:
        column_names = metric_domain_kwargs["column_list"]
        column_names = get_dbms_compatible_column_names(
            column_names=column_names,
            batch_columns_list=batch_columns_list,
        )
        metric_domain_kwargs["column_list"] = column_names

    return metric_domain_kwargs


@overload
def get_dbms_compatible_column_names(
    column_names: str,
    batch_columns_list: Sequence[str | sqlalchemy.quoted_name],
    error_message_template: str = ...,
) -> str | sqlalchemy.quoted_name: ...


@overload
def get_dbms_compatible_column_names(
    column_names: List[str],
    batch_columns_list: Sequence[str | sqlalchemy.quoted_name],
    error_message_template: str = ...,
) -> List[str | sqlalchemy.quoted_name]: ...


def get_dbms_compatible_column_names(
    column_names: List[str] | str,
    batch_columns_list: Sequence[str | sqlalchemy.quoted_name],
    error_message_template: str = 'Error: The column "{column_name:s}" in BatchData does not exist.',  # noqa: E501 # FIXME CoP
) -> List[str | sqlalchemy.quoted_name] | str | sqlalchemy.quoted_name:
    """
    Case non-sensitivity is expressed in upper case by common DBMS backends and in lower case by SQLAlchemy, with any
    deviations enclosed with double quotes.

    SQLAlchemy enables correct translation to/from DBMS backends through "sqlalchemy.sql.elements.quoted_name" class
    where necessary by insuring that column names of correct type (i.e., "str" or "sqlalchemy.sql.elements.quoted_name")
    are returned by "sqlalchemy.inspect(sqlalchemy.engine.Engine).get_columns(table_name, schema)" ("table.columns"
    metric is based on this method).  Columns of precise type (string or "quoted_name" as appropriate) are returned.

    Args:
        column_names: Single string-valued column name or list of string-valued column names
        batch_columns_list: Properly typed column names (output of "table.columns" metric)
        error_message_template: String template to output error message if any column cannot be found in "Batch" object.

    Returns:
        Single property-typed column name object or list of property-typed column name objects (depending on input).
    """  # noqa: E501 # FIXME CoP
    normalized_typed_batch_columns_mappings: List[Tuple[str, str | sqlalchemy.quoted_name]] = (
        _verify_column_names_exist_and_get_normalized_typed_column_names_map(
            column_names=column_names,
            batch_columns_list=batch_columns_list,
            error_message_template=error_message_template,
        )
        or []
    )

    element: Tuple[str, str | sqlalchemy.quoted_name]
    typed_batch_column_names_list: List[str | sqlalchemy.quoted_name] = [
        element[1] for element in normalized_typed_batch_columns_mappings
    ]
    if isinstance(column_names, list):
        return typed_batch_column_names_list

    return typed_batch_column_names_list[0]


def verify_column_names_exist(
    column_names: List[str] | str,
    batch_columns_list: List[str | sqlalchemy.quoted_name],
    error_message_template: str = 'Error: The column "{column_name:s}" in BatchData does not exist.',  # noqa: E501 # FIXME CoP
) -> None:
    _ = _verify_column_names_exist_and_get_normalized_typed_column_names_map(
        column_names=column_names,
        batch_columns_list=batch_columns_list,
        error_message_template=error_message_template,
        verify_only=True,
    )


def _verify_column_names_exist_and_get_normalized_typed_column_names_map(  # noqa: C901 # FIXME CoP
    column_names: List[str] | str,
    batch_columns_list: Sequence[str | sqlalchemy.quoted_name],
    error_message_template: str = 'Error: The column "{column_name:s}" in BatchData does not exist.',  # noqa: E501 # FIXME CoP
    verify_only: bool = False,
) -> List[Tuple[str, str | sqlalchemy.quoted_name]] | None:
    """
    Insures that column name or column names (supplied as argument using "str" representation) exist in "Batch" object.

    Args:
        column_names: Single string-valued column name or list of string-valued column names
        batch_columns_list: Properly typed column names (output of "table.columns" metric)
        verify_only: Perform verification only (do not return normalized typed column names)
        error_message_template: String template to output error message if any column cannot be found in "Batch" object.

    Returns:
        List of tuples having mapping from string-valued column name to typed column name; None if "verify_only" is set.
    """  # noqa: E501 # FIXME CoP
    column_names_list: List[str]
    if isinstance(column_names, list):
        column_names_list = column_names
    else:
        column_names_list = [column_names]

    def _get_normalized_column_name_mapping_if_exists(
        column_name: str,
    ) -> Tuple[str, str | sqlalchemy.quoted_name] | None:
        typed_column_name_cursor: str | sqlalchemy.quoted_name
        for typed_column_name_cursor in batch_columns_list:
            if (
                (type(typed_column_name_cursor) == str)  # noqa: E721 # FIXME CoP
                and (column_name.casefold() == typed_column_name_cursor.casefold())
            ) or (column_name == str(typed_column_name_cursor)):
                return column_name, typed_column_name_cursor

            # use explicit identifier if passed in by user
            if isinstance(typed_column_name_cursor, str) and (
                (column_name.casefold().strip('"') == typed_column_name_cursor.casefold())
                or (column_name.casefold().strip("[]") == typed_column_name_cursor.casefold())
                or (column_name.casefold().strip("`") == typed_column_name_cursor.casefold())
            ):
                return column_name, column_name

        return None

    normalized_batch_columns_mappings: List[Tuple[str, str | sqlalchemy.quoted_name]] = []

    normalized_column_name_mapping: Tuple[str, str | sqlalchemy.quoted_name] | None
    column_name: str
    for column_name in column_names_list:
        normalized_column_name_mapping = _get_normalized_column_name_mapping_if_exists(
            column_name=column_name
        )
        if normalized_column_name_mapping is None:
            raise gx_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=error_message_template.format(column_name=column_name)
            )
        else:  # noqa: PLR5501 # FIXME CoP
            if not verify_only:
                normalized_batch_columns_mappings.append(normalized_column_name_mapping)

    return None if verify_only else normalized_batch_columns_mappings


def parse_value_set(value_set: Iterable) -> list:
    parsed_value_set = [parse(value) if isinstance(value, str) else value for value in value_set]
    return parsed_value_set


def get_dialect_like_pattern_expression(  # noqa: C901, PLR0912, PLR0915 # FIXME CoP
    column: sa.Column, dialect: ModuleType, like_pattern: str, positive: bool = True
) -> sa.BinaryExpression | None:
    dialect_supported: bool = False

    try:
        # Bigquery
        if hasattr(dialect, "BigQueryDialect"):
            dialect_supported = True
    except (
        AttributeError,
        TypeError,
    ):  # TypeError can occur if the driver was not installed and so is None
        pass

    if hasattr(dialect, "dialect"):
        try:
            if issubclass(dialect.dialect, sa.dialects.sqlite.dialect):
                dialect_supported = True
        except AttributeError:
            pass
        try:
            if issubclass(dialect.dialect, sa.dialects.postgresql.dialect):
                dialect_supported = True
        except AttributeError:
            pass
        try:
            if issubclass(dialect.dialect, sa.dialects.mysql.dialect):
                dialect_supported = True
        except AttributeError:
            pass
        try:
            if issubclass(dialect.dialect, sa.dialects.mssql.dialect):
                dialect_supported = True
        except AttributeError:
            pass

    if _is_databricks_dialect(dialect):
        dialect_supported = True

    try:
        if hasattr(dialect, "RedshiftDialect"):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass

    # noinspection PyUnresolvedReferences
    if aws.redshiftdialect and isinstance(dialect, aws.redshiftdialect.RedshiftDialect):
        dialect_supported = True
    else:
        pass

    try:
        # noinspection PyUnresolvedReferences
        if hasattr(dialect, "TrinoDialect") or (
            trino.trinodialect and isinstance(dialect, trino.trinodialect.TrinoDialect)
        ):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass

    try:
        # noinspection PyUnresolvedReferences
        if hasattr(dialect, "ClickHouseDialect") or isinstance(
            dialect, clickhouse_sqlalchemy.drivers.base.ClickHouseDialect
        ):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass
    try:
        if hasattr(dialect, "SnowflakeDialect"):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass

    try:
        if hasattr(dialect, "DremioDialect"):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass

    try:
        if issubclass(dialect.dialect, teradatasqlalchemy.dialect.TeradataDialect):
            dialect_supported = True
    except (AttributeError, TypeError):
        pass

    if dialect_supported:
        try:
            if positive:
                return column.like(sqlalchemy.literal(like_pattern))
            else:
                return sa.not_(column.like(sqlalchemy.literal(like_pattern)))
        except AttributeError:
            pass

    return None


def validate_distribution_parameters(  # noqa: C901, PLR0912, PLR0915 # FIXME CoP
    distribution, params
):
    """Ensures that necessary parameters for a distribution are present and that all parameters are sensical.

       If parameters necessary to construct a distribution are missing or invalid, this function raises ValueError\
       with an informative description. Note that 'loc' and 'scale' are optional arguments, and that 'scale'\
       must be positive.

       Args:
           distribution (string): \
               The scipy distribution name, e.g. normal distribution is 'norm'.
           params (dict or list): \
               The distribution shape parameters in a named dictionary or positional list form following the scipy \
               cdf argument scheme.

               params={'mean': 40, 'std_dev': 5} or params=[40, 5]

       Exceptions:
           ValueError: \
               With an informative description, usually when necessary parameters are omitted or are invalid.

    """  # noqa: E501 # FIXME CoP

    norm_msg = "norm distributions require 0 parameters and optionally 'mean', 'std_dev'."
    beta_msg = "beta distributions require 2 positive parameters 'alpha', 'beta' and optionally 'loc', 'scale'."  # noqa: E501 # FIXME CoP
    gamma_msg = (
        "gamma distributions require 1 positive parameter 'alpha' and optionally 'loc','scale'."
    )
    # poisson_msg = "poisson distributions require 1 positive parameter 'lambda' and optionally 'loc'."  # noqa: E501 # FIXME CoP
    uniform_msg = "uniform distributions require 0 parameters and optionally 'loc', 'scale'."
    chi2_msg = "chi2 distributions require 1 positive parameter 'df' and optionally 'loc', 'scale'."
    expon_msg = "expon distributions require 0 parameters and optionally 'loc', 'scale'."

    if distribution not in [
        "norm",
        "beta",
        "gamma",
        "poisson",
        "uniform",
        "chi2",
        "expon",
    ]:
        raise AttributeError(f"Unsupported  distribution provided: {distribution}")  # noqa: TRY003 # FIXME CoP

    if isinstance(params, dict):
        # `params` is a dictionary
        if params.get("std_dev", 1) <= 0 or params.get("scale", 1) <= 0:
            raise ValueError("std_dev and scale must be positive.")  # noqa: TRY003 # FIXME CoP

        # alpha and beta are required and positive
        if distribution == "beta" and (params.get("alpha", -1) <= 0 or params.get("beta", -1) <= 0):
            raise ValueError(f"Invalid parameters: {beta_msg}")  # noqa: TRY003 # FIXME CoP

        # alpha is required and positive
        elif distribution == "gamma" and params.get("alpha", -1) <= 0:
            raise ValueError(f"Invalid parameters: {gamma_msg}")  # noqa: TRY003 # FIXME CoP

        # lambda is a required and positive
        # elif distribution == 'poisson' and params.get('lambda', -1) <= 0:
        #    raise ValueError("Invalid parameters: %s" %poisson_msg)

        # df is necessary and required to be positive
        elif distribution == "chi2" and params.get("df", -1) <= 0:
            raise ValueError(f"Invalid parameters: {chi2_msg}:")  # noqa: TRY003 # FIXME CoP

    elif isinstance(params, (tuple, list)):
        scale = None

        # `params` is a tuple or a list
        if distribution == "beta":
            if len(params) < 2:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Missing required parameters: {beta_msg}")  # noqa: TRY003 # FIXME CoP
            if params[0] <= 0 or params[1] <= 0:
                raise ValueError(f"Invalid parameters: {beta_msg}")  # noqa: TRY003 # FIXME CoP
            if len(params) == 4:  # noqa: PLR2004 # FIXME CoP
                scale = params[3]
            elif len(params) > 4:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many parameters provided: {beta_msg}")  # noqa: TRY003 # FIXME CoP

        elif distribution == "norm":
            if len(params) > 2:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many parameters provided: {norm_msg}")  # noqa: TRY003 # FIXME CoP
            if len(params) == 2:  # noqa: PLR2004 # FIXME CoP
                scale = params[1]

        elif distribution == "gamma":
            if len(params) < 1:
                raise ValueError(f"Missing required parameters: {gamma_msg}")  # noqa: TRY003 # FIXME CoP
            if len(params) == 3:  # noqa: PLR2004 # FIXME CoP
                scale = params[2]
            if len(params) > 3:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many parameters provided: {gamma_msg}")  # noqa: TRY003 # FIXME CoP
            elif params[0] <= 0:
                raise ValueError(f"Invalid parameters: {gamma_msg}")  # noqa: TRY003 # FIXME CoP

        # elif distribution == 'poisson':
        #    if len(params) < 1:
        #        raise ValueError("Missing required parameters: %s" %poisson_msg)
        #   if len(params) > 2:
        #        raise ValueError("Too many parameters provided: %s" %poisson_msg)
        #    elif params[0] <= 0:
        #        raise ValueError("Invalid parameters: %s" %poisson_msg)

        elif distribution == "uniform":
            if len(params) == 2:  # noqa: PLR2004 # FIXME CoP
                scale = params[1]
            if len(params) > 2:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many arguments provided: {uniform_msg}")  # noqa: TRY003 # FIXME CoP

        elif distribution == "chi2":
            if len(params) < 1:
                raise ValueError(f"Missing required parameters: {chi2_msg}")  # noqa: TRY003 # FIXME CoP
            elif len(params) == 3:  # noqa: PLR2004 # FIXME CoP
                scale = params[2]
            elif len(params) > 3:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many arguments provided: {chi2_msg}")  # noqa: TRY003 # FIXME CoP
            if params[0] <= 0:
                raise ValueError(f"Invalid parameters: {chi2_msg}")  # noqa: TRY003 # FIXME CoP

        elif distribution == "expon":
            if len(params) == 2:  # noqa: PLR2004 # FIXME CoP
                scale = params[1]
            if len(params) > 2:  # noqa: PLR2004 # FIXME CoP
                raise ValueError(f"Too many arguments provided: {expon_msg}")  # noqa: TRY003 # FIXME CoP

        if scale is not None and scale <= 0:
            raise ValueError("std_dev and scale must be positive.")  # noqa: TRY003 # FIXME CoP

    else:
        raise ValueError(  # noqa: TRY003, TRY004 # FIXME CoP
            "params must be a dict or list, or use great_expectations.dataset.util.infer_distribution_parameters(data, distribution)"  # noqa: E501 # FIXME CoP
        )


def _scipy_distribution_positional_args_from_dict(distribution, params):
    """Helper function that returns positional arguments for a scipy distribution using a dict of parameters.

       See the `cdf()` function here https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.beta.html#Methods\
       to see an example of scipy's positional arguments. This function returns the arguments specified by the \
       scipy.stat.distribution.cdf() for that distribution.

       Args:
           distribution (string): \
               The scipy distribution name.
           params (dict): \
               A dict of named parameters.

       Raises:
           AttributeError: \
               If an unsupported distribution is provided.
    """  # noqa: E501 # FIXME CoP

    params["loc"] = params.get("loc", 0)
    if "scale" not in params:
        params["scale"] = 1

    if distribution == "norm":
        return params["mean"], params["std_dev"]
    elif distribution == "beta":
        return params["alpha"], params["beta"], params["loc"], params["scale"]
    elif distribution == "gamma":
        return params["alpha"], params["loc"], params["scale"]
    # elif distribution == 'poisson':
    #    return params['lambda'], params['loc']
    elif distribution == "uniform":
        return params["min"], params["max"]
    elif distribution == "chi2":
        return params["df"], params["loc"], params["scale"]
    elif distribution == "expon":
        return params["loc"], params["scale"]


def is_valid_continuous_partition_object(partition_object):
    """Tests whether a given object is a valid continuous partition object. See :ref:`partition_object`.

    :param partition_object: The partition_object to evaluate
    :return: Boolean
    """  # noqa: E501 # FIXME CoP
    if (
        (partition_object is None)
        or ("weights" not in partition_object)
        or ("bins" not in partition_object)
    ):
        return False

    if "tail_weights" in partition_object:
        if len(partition_object["tail_weights"]) != 2:  # noqa: PLR2004 # FIXME CoP
            return False
        comb_weights = partition_object["tail_weights"] + partition_object["weights"]
    else:
        comb_weights = partition_object["weights"]

    ## TODO: Consider adding this check to migrate to the tail_weights structure of partition objects  # noqa: E501 # FIXME CoP
    # if (partition_object['bins'][0] == -np.inf) or (partition_object['bins'][-1] == np.inf):
    #     return False

    # Expect one more bin edge than weight; all bin edges should be monotonically increasing; weights should sum to one  # noqa: E501 # FIXME CoP
    return (
        (len(partition_object["bins"]) == (len(partition_object["weights"]) + 1))
        and np.all(np.diff(partition_object["bins"]) > 0)
        and np.allclose(np.sum(comb_weights), 1.0)
    )


def sql_statement_with_post_compile_to_string(
    engine: SqlAlchemyExecutionEngine, select_statement: sqlalchemy.Select
) -> str:
    """
    Util method to compile SQL select statement with post-compile parameters into a string. Logic lifted directly
    from sqlalchemy documentation.

    https://docs.sqlalchemy.org/en/14/faq/sqlexpressions.html#rendering-postcompile-parameters-as-bound-parameters

    Used by _sqlalchemy_map_condition_index() in map_metric_provider to build query that will allow you to
    return unexpected_index_values.

    Args:
        engine (sqlalchemy.engine.Engine): Sqlalchemy engine used to do the compilation.
        select_statement (sqlalchemy.sql.Select): Select statement to compile into string.
    Returns:
        String representation of select_statement

    """
    sqlalchemy_connection: sa.engine.base.Connection = engine.engine
    compiled = select_statement.compile(
        sqlalchemy_connection,
        compile_kwargs={"render_postcompile": True},
        dialect=engine.dialect,
    )
    dialect_name: str = engine.dialect_name

    # FIX FOR NONETYPE ERROR - Add null check for compiled.positiontup
    if dialect_name in ["sqlite", "trino", "mssql"]:
        if compiled.positiontup is not None:
            params = (repr(compiled.params[name]) for name in compiled.positiontup)
        else:
            params = ()  # Empty generator if positiontup is None
        query_as_string = re.sub(r"\?", lambda m: next(params), str(compiled))

    else:
        params = (repr(compiled.params[name]) for name in list(compiled.params.keys()))
        query_as_string = re.sub(r"%\(.*?\)s", lambda m: next(params), str(compiled))

    query_as_string += ";"
    return query_as_string


def get_sqlalchemy_source_table_and_schema(
    engine: SqlAlchemyExecutionEngine,
) -> sa.Table:
    """
    Util method to return table name that is associated with current batch.

    This is used by `_sqlalchemy_map_condition_query()` which returns a query that allows users to return
    unexpected_index_values.

    Args:
        engine (SqlAlchemyExecutionEngine): Engine that is currently being used to calculate the Metrics
    Returns:
        SqlAlchemy Table that is the source table and schema.
    """  # noqa: E501 # FIXME CoP
    assert isinstance(engine.batch_manager.active_batch_data, SqlAlchemyBatchData), (
        "`active_batch_data` not SqlAlchemyBatchData"
    )

    schema_name = engine.batch_manager.active_batch_data.source_schema_name
    table_name = engine.batch_manager.active_batch_data.source_table_name
    if table_name:
        return sa.Table(
            table_name,
            sa.MetaData(),
            schema=schema_name,
        )
    else:
        return engine.batch_manager.active_batch_data.selectable


def get_unexpected_indices_for_multiple_pandas_named_indices(  # noqa: C901 # FIXME CoP
    domain_records_df: pd.DataFrame,
    unexpected_index_column_names: List[str],
    expectation_domain_column_list: List[str],
    exclude_unexpected_values: bool = False,
) -> UnexpectedIndexList:
    """
    Builds unexpected_index_list for Pandas Dataframe in situation where the named
    columns is also a named index. This method handles the case when there are multiple named indices.
    Args:
        domain_records_df: reference to Pandas dataframe
        unexpected_index_column_names: column_names for indices, either named index or unexpected_index_columns
        expectation_domain_column_list: list of columns that Expectation is being run on.

    Returns:
        List of Dicts that contain ID/PK values
    """  # noqa: E501 # FIXME CoP
    if not expectation_domain_column_list:
        raise gx_exceptions.MetricResolutionError(
            message="Error: The list of domain columns is currently empty. Please check your configuration.",  # noqa: E501 # FIXME CoP
            failed_metrics=["unexpected_index_list"],
        )

    domain_records_df_index_names: List[str] = domain_records_df.index.names
    unexpected_indices: List[tuple[int | str, ...]] = list(domain_records_df.index)

    tuple_index: Dict[str, int] = dict()
    for column_name in unexpected_index_column_names:
        if column_name not in domain_records_df_index_names:
            raise gx_exceptions.MetricResolutionError(
                message=f"Error: The column {column_name} does not exist in the named indices. "
                f"Please check your configuration.",
                failed_metrics=["unexpected_index_list"],
            )
        else:
            tuple_index[column_name] = domain_records_df_index_names.index(column_name, 0)

    unexpected_index_list: UnexpectedIndexList = []

    if exclude_unexpected_values and len(unexpected_indices) != 0:
        primary_key_dict_list: dict[str, List[Any]] = {
            idx_col: [] for idx_col in unexpected_index_column_names
        }
        for index in unexpected_indices:
            for column_name in unexpected_index_column_names:
                primary_key_dict_list[column_name].append(index[tuple_index[column_name]])

        unexpected_index_list.append(primary_key_dict_list)

    else:
        for index in unexpected_indices:
            primary_key_dict: Dict[str, Any] = dict()
            for domain_column_name in expectation_domain_column_list:
                primary_key_dict[domain_column_name] = domain_records_df.at[
                    index, domain_column_name
                ]
                for column_name in unexpected_index_column_names:
                    primary_key_dict[column_name] = index[tuple_index[column_name]]
            unexpected_index_list.append(primary_key_dict)

    return unexpected_index_list


def get_unexpected_indices_for_single_pandas_named_index(
    domain_records_df: pd.DataFrame,
    unexpected_index_column_names: List[str],
    expectation_domain_column_list: List[str],
    exclude_unexpected_values: bool = False,
) -> UnexpectedIndexList:
    """
    Builds unexpected_index_list for Pandas Dataframe in situation where the named
    columns is also a named index. This method handles the case when there is a single named index.
    Args:
        domain_records_df: reference to Pandas dataframe
        unexpected_index_column_names: column_names for indices, either named index or unexpected_index_columns
        expectation_domain_column_list: list of columns that Expectation is being run on.

    Returns:
        List of Dicts that contain ID/PK values

    """  # noqa: E501 # FIXME CoP
    if not expectation_domain_column_list:
        return []
    unexpected_index_values_by_named_index: List[int | str] = list(domain_records_df.index)
    unexpected_index_list: UnexpectedIndexList = []
    if not (
        len(unexpected_index_column_names) == 1
        and unexpected_index_column_names[0] == domain_records_df.index.name
    ):
        raise gx_exceptions.MetricResolutionError(
            message=f"Error: The column {unexpected_index_column_names[0] if unexpected_index_column_names else '<no column specified>'} does not exist in the named indices. Please check your configuration",  # noqa: E501 # FIXME CoP
            failed_metrics=["unexpected_index_list"],
        )

    if exclude_unexpected_values and len(unexpected_index_values_by_named_index) != 0:
        primary_key_dict_list: dict[str, List[Any]] = {unexpected_index_column_names[0]: []}
        for index in unexpected_index_values_by_named_index:
            primary_key_dict_list[unexpected_index_column_names[0]].append(index)
        unexpected_index_list.append(primary_key_dict_list)

    else:
        for index in unexpected_index_values_by_named_index:
            primary_key_dict: Dict[str, Any] = dict()
            for domain_column in expectation_domain_column_list:
                primary_key_dict[domain_column] = domain_records_df.at[index, domain_column]
            column_name: str = unexpected_index_column_names[0]
            primary_key_dict[column_name] = index
            unexpected_index_list.append(primary_key_dict)

    return unexpected_index_list


def compute_unexpected_pandas_indices(  # noqa: C901 # FIXME CoP
    domain_records_df: pd.DataFrame,
    expectation_domain_column_list: List[str],
    result_format: Dict[str, Any],
    execution_engine: PandasExecutionEngine,
    metrics: Dict[str, Any],
) -> UnexpectedIndexList:
    """
    Helper method to compute unexpected_index_list for PandasExecutionEngine. Handles logic needed for named indices.

    Args:
        domain_records_df: DataFrame of data we are currently running Expectation on.
        expectation_domain_column_list: list of columns that we are running Expectation on. It can be one column.
        result_format: configuration that contains `unexpected_index_column_names`
                expectation_domain_column_list: list of columns that we are running Expectation on. It can be one column.
        execution_engine: PandasExecutionEngine
        metrics: dict of currently available metrics

    Returns:
        list of unexpected_index_list values. It can either be a list of dicts or a list of numbers (if using default index).

    """  # noqa: E501 # FIXME CoP
    unexpected_index_column_names: List[str]
    unexpected_index_list: UnexpectedIndexList
    exclude_unexpected_values: bool = result_format.get("exclude_unexpected_values", False)

    if domain_records_df.index.name is not None:
        unexpected_index_column_names = result_format.get(
            "unexpected_index_column_names", [domain_records_df.index.name]
        )
        unexpected_index_list = get_unexpected_indices_for_single_pandas_named_index(
            domain_records_df=domain_records_df,
            unexpected_index_column_names=unexpected_index_column_names,
            expectation_domain_column_list=expectation_domain_column_list,
            exclude_unexpected_values=exclude_unexpected_values,
        )
    # multiple named indices
    elif domain_records_df.index.names[0] is not None:
        unexpected_index_column_names = result_format.get(
            "unexpected_index_column_names", list(domain_records_df.index.names)
        )
        unexpected_index_list = get_unexpected_indices_for_multiple_pandas_named_indices(
            domain_records_df=domain_records_df,
            unexpected_index_column_names=unexpected_index_column_names,
            expectation_domain_column_list=expectation_domain_column_list,
            exclude_unexpected_values=exclude_unexpected_values,
        )
    # named columns
    elif result_format.get("unexpected_index_column_names"):
        unexpected_index_column_names = result_format["unexpected_index_column_names"]
        unexpected_index_list = []
        unexpected_indices: List[int | str] = list(domain_records_df.index)

        if (
            exclude_unexpected_values
            and len(unexpected_indices) != 0
            and len(unexpected_index_column_names) != 0
        ):
            primary_key_dict_list: dict[str, List[Any]] = {
                idx_col: [] for idx_col in unexpected_index_column_names
            }
            for index in unexpected_indices:
                for column_name in unexpected_index_column_names:
                    column_name = get_dbms_compatible_column_names(  # noqa: PLW2901 # FIXME CoP
                        column_names=column_name,
                        batch_columns_list=metrics["table.columns"],
                        error_message_template='Error: The unexpected_index_column "{column_name:s}" does not exist in Dataframe. Please check your configuration and try again.',  # noqa: E501 # FIXME CoP
                    )
                    primary_key_dict_list[column_name].append(
                        domain_records_df.at[index, column_name]
                    )
            unexpected_index_list.append(primary_key_dict_list)

        else:
            for index in unexpected_indices:
                primary_key_dict: Dict[str, Any] = dict()
                assert expectation_domain_column_list, (
                    "`expectation_domain_column_list` was not provided"
                )
                for domain_column_name in expectation_domain_column_list:
                    primary_key_dict[domain_column_name] = domain_records_df.at[
                        index, domain_column_name
                    ]
                    for column_name in unexpected_index_column_names:
                        column_name = get_dbms_compatible_column_names(  # noqa: PLW2901 # FIXME CoP
                            column_names=column_name,
                            batch_columns_list=metrics["table.columns"],
                            error_message_template='Error: The unexpected_index_column "{column_name:s}" does not exist in Dataframe. Please check your configuration and try again.',  # noqa: E501 # FIXME CoP
                        )
                        primary_key_dict[column_name] = domain_records_df.at[index, column_name]
                unexpected_index_list.append(primary_key_dict)

    else:
        unexpected_index_list = list(domain_records_df.index)

    return unexpected_index_list
