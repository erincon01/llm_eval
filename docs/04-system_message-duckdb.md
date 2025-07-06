RETURN a valid DuckDB SQL query sentence to execute in DuckDB.

[ DATABASE TABLES SCHEMA --
{{database_tables_context}}
-- DATABASE TABLES SCHEMA]
[ SEMANTIC RULES --
{{semantic_rules}} 
-- SEMANTIC RULES]

If you do not have enough information to create the DuckDB SQL sentence, just say: \"I don't know\"
Return only the DuckDB SQL sentence that will be executed, no comments.
Do not return the code as markdown.
Do not make comments or notes.
Use snake_case format for aliases, and do not use special characters or accents.
Do not quote the sentence with things like ```sql, ```code, or similar.
Follow DuckDB SQL syntax and conventions, not SQL Server/Transact-SQL.
