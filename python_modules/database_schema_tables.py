import yaml


class Database_schema_tables:
    def __init__(self, yaml_file):
        self.yaml_file = yaml_file
        self.tables = []
        self.load_schema()

    def load_schema(self):
        """Load the database schema from the YAML file."""
        try:
            with open(self.yaml_file, "r") as file:
                data = yaml.safe_load(file)
                self.tables = data.get("tables", [])
        except FileNotFoundError:
            print(f"Error: File {self.yaml_file} not found.")
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")

    def get_table_names(self):
        """Return a list of all table names in the schema."""
        return [table["name"] for table in self.tables]

    def get_table_script(self, table_name):
        """Return the script for a specific table by name."""
        for table in self.tables:
            if table["name"] == table_name:
                return table.get("script", "")
        return None

    def get_all_tables_scripts(self):
        """Return a list of all tables' scripts."""
        return [table.get("script", "") for table in self.tables]

    def add_table(self, table_name, script):
        """Add a new table to the schema."""
        self.tables.append({"name": table_name, "script": script})
        self.save_schema()

    def save_schema(self):
        """Save the current schema back to the YAML file."""
        try:
            with open(self.yaml_file, "w") as file:
                yaml.dump({"tables": self.tables}, file, default_flow_style=False)
        except Exception as e:
            print(f"Error saving YAML file: {e}")
