__author__ = "Jan Cerezo"
__credits__ = ["Julián Arenas-Guerrero","Ioannis Dasoulas","Jan Cerezo"]

__license__ = "Apache-2.0"
__maintainer__ = "Ioannis Dasoulas"
__email__ = "ioannis.dasoulas@kuleuven.be"


import os

import morph_kgc
import pandas as pd
from rdflib import Literal, URIRef
from rdflib.namespace import RDFS

def test_RMLTC0016a():
    test_csv_path = mapping_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'test.csv')
    df = pd.read_csv(test_csv_path)
    
    data_dict = {"variable1": df}
    mapping_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mapping.ttl')
    config = f"[DataSource]\nmappings={mapping_path}"
    g_morph = morph_kgc.materialize(config, data_dict)

    assert len(g_morph) == 1
    assert (
        URIRef("http://example.com/4"),
        RDFS.label,
        Literal("f"),
    ) in g_morph
