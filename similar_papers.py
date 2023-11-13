from merge_graphs import list_files
from rdflib import Graph, Namespace, RDF, URIRef, BNode, Literal, XSD
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility, db
import os


def extract_embedding_from_graph(graph: Graph):
    bn = Namespace("https://w3id.org/ocs/ont/papers/")
    graph.bind("", bn)
    embedding = eval(str(list(graph.triples((None, bn.hasWordEmbedding, None)))[0][2]))
    return embedding

def extract_paper_uri(graph: Graph):
    fabio = Namespace("http://purl.org/spar/fabio/")
    graph.bind("fabio", fabio)
    paper_uri = str(list(graph.triples((None, RDF.type, fabio.ResearchPaper)))[0][0])
    return paper_uri

def extract_title_from_graph(graph: Graph):
    pred_uri = URIRef("http://purl.org/dc/terms/title")
    title_triple = list(graph.triples((None, pred_uri, None)))[0]
    object_literal = str(title_triple[2])
    return object_literal



def main():

    connections.connect(
        alias="default",
        user='username',
        password='password',
        host='localhost',
        port='19530'
    )

    database_name = "papers"
    if database_name in db.list_database():
        db.create_database(database_name)
        
    db.using_database(database_name)

    paper_id = FieldSchema(
        name="paper_id",
        dtype=DataType.VARCHAR,
        is_primary=True,
        max_length=200
    )
    paper_title = FieldSchema(
        name="paper_title",
        dtype=DataType.VARCHAR,
        max_length=200
    )
    embedding_field = FieldSchema(
        name="embedding_field",
        dtype=DataType.FLOAT_VECTOR,
        dim=768
    )

    collection_schema = CollectionSchema(
        fields=[paper_id, embedding_field, paper_title],
        description="Paper similarity finder",
        enable_dynamic_field=True
    )
    collection_name = "research_papers"

    collection = Collection(
        name=collection_name,
        schema=collection_schema,
        using='default',
        shards_num=2
    )

    file_list = list_files("/home/input_ttl_files")

    for ttl_file in file_list:
        g = Graph()
        g.parse(os.path.join(ttl_file), format="ttl")

        embedding = extract_embedding_from_graph(g)
        paper_uri = extract_paper_uri(g)
        title = extract_title_from_graph(g)

        data = [[paper_uri], [embedding], [title]]
        collection.insert(data)

    index_params = {
        "metric_type":"COSINE",
        "index_type":"IVF_FLAT",
        "params":{"nlist":768}
    }

    collection.create_index(
        field_name="embedding_field", 
        index_params=index_params
    )

    utility.index_building_progress("research_papers")

    collection = Collection("research_papers")
    collection.load()

    search_params = {
        "metric_type": "COSINE", 
        "offset": 0, 
        "ignore_growing": False, 
        "params": {"nprobe": 10}
    }

    g_sim = Graph()
    base = Namespace("https://w3id.org/ocs/ont/papers/")

    for ttl_file in file_list:
        g = Graph()
        g.parse(os.path.join(ttl_file), format="ttl")

        embedding = extract_embedding_from_graph(g)
        paper_uri = extract_paper_uri(g)

    
        results = collection.search(
            data=[embedding], 
            anns_field="embedding_field", 
            param=search_params,
            limit=10,
            expr=None,
            output_fields=['paper_title', 'distance']
        )

        for res in results[0]:

            blank_node = BNode()
            g_sim.add((paper_uri, base.hasRelatedPapers, blank_node))
            
            sim_paper_uri = res.id
            sim_score = res.distance
            
            g_sim.add((blank_node, base.hasOpencsUID, sim_paper_uri))
            g_sim.add((blank_node, base.similarityScore, Literal(sim_score, datatype=XSD.integer)))


    with open("/home/output/similarity_graph.ttl", "wb") as file:
        g_sim = g_sim.serialize(format="turtle")
        if isinstance(g_sim, str):
            g_sim = g_sim.encode()
        file.write(g_sim)

          

if __name__ == "__main__":
    main()