import os
from pathlib import Path
from typing import List, Dict

import duckdb
from duckdb import BinderException, CastException, CatalogException, ConnectionException, ConstraintException, DataError, ConversionException

from dindex_store.common import ProfileIndex


class ProfileIndexDuckDB(ProfileIndex):

    def __init__(self, config: Dict, load=False, force=False) -> None:
        ProfileIndexDuckDB._validate_config(config)
        self.config = config
        db_path = Path(config['ver_base_path']) / Path(config['profile_duckdb_database_name'])
        self.conn = duckdb.connect(database=str(db_path))
        self.schema = ""

        if not load:
            profile_schema_path = Path(config['ver_base_path'] / config['profile_schema_name']).absolute()
            with open(profile_schema_path) as f:
                self.schema = f.read()
            try:
                if force:
                    profile_table_name = config["profile_table_name"]
                    q = f"DROP TABLE IF EXISTS {profile_table_name};"
                    self.conn.execute(q)
                for statement in self.schema.split(";"):
                    self.conn.execute(statement)
            except:
                print("An error has occurred when reading the schema")
                raise

    def add_profile(self, node: Dict) -> bool:
        try:
            profile_table = self.conn.table(self.config["profile_table_name"])
            profile_table.insert(node.values())
            return True
        except BinderException as be:
            print(f"An error has occured when trying to add profile: {be}")
            return False
        except CastException as ce:
            print(f"An error has occured when trying to add profile: {ce}")
            return False
        except CatalogException as cae:
            print(f"An error has occured when trying to add profile: {cae}")
            return False
        except ConnectionException as coe:
            print(f"An error has occured when trying to add profile: {coe}")
            return False
        except ConstraintException as cone:
            print(f"An error has occured when trying to add profile: {cone}")
            return False
        except ConversionException as conve:
            print(f"An error has occured when trying to add profile: {conve}")
            return False
        except DataError as de:
            print(f"An error has occured when trying to add profile: {de}")
            return False

    def get_filtered_profiles_from_table(self, table_name, desired_attributes: List[str]):
        profile_table = self.config["profile_table_name"]
        project_list = ",".join(desired_attributes)
        try:
            query = f"SELECT {project_list} FROM {profile_table} WHERE sourcename = '{table_name}'"
            result = self.conn.execute(query)
            return result.fetchall()
        except BinderException as be:
            print(f"""An error has occured when trying to get profile: {be}""")
            return False

    def get_filtered_profiles_from_nids(self, nids, desired_attributes: List[str]):
        project_list = ",".join(desired_attributes)
        predicate = "OR id = ".join([str(n) for n in nids])
        try:
            profile_table = self.config["profile_table_name"]
            query = f"""SELECT {project_list} FROM {profile_table} WHERE id = {predicate}"""
            results = self.conn.execute(query)
            return results.fetchall()
        except BinderException as be:
            print(f"""An error has occured when trying to get profile {be}""")
            return False
        
    def get_profile(self, node_id: int) -> Dict:
        pass
    
    def get_minhashes(self) -> Dict:
        # Get all profiles with minhash
        profile_table = self.conn.table(self.config["profile_table_name"])
        return profile_table.filter('minhash IS NOT NULL') \
            .project('id, decode(minhash)') \
            .to_df() \
            .rename(columns={'decode(minhash)': 'minhash'}) \
            .to_dict(orient='records')

    @classmethod
    def _validate_config(cls, config):
        assert "profile_schema_name" in config, "Error: schema_path is missing"
        profile_schema_path = Path(config['ver_base_path'] / config['profile_schema_name']).absolute()
        if not os.path.isfile(profile_schema_path):
            raise ValueError("The path does not exist, or is not a file")
        
        assert "profile_table_name" in config


if __name__ == "__main__":
    print("ProfileIndexDuckDB")

    import config

    cnf = dict(config)
    index = ProfileIndexDuckDB(cnf)

    # FIXME: what to do if this file is invoked individually?
