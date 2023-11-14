from merge_graphs import list_files
from rdflib import Graph, Namespace, RDF, URIRef, BNode, Literal, XSD
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility, db
from kneed import KneeLocator
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
        host='milvus-standalone',
        port='19530'
    )
    
    database_name = "papers"
    collection_name = "research_papers"

    if database_name not in db.list_database():
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

    collection = Collection(
        name=collection_name,
        schema=collection_schema,
        using='default',
        shards_num=2
    )

    file_list = list_files("/home/input_ttl_files")

    print("Adding vectors to collection...")

    for ttl_file in file_list:
        g = Graph()
        g.parse(os.path.join(ttl_file), format="ttl")

        embedding = extract_embedding_from_graph(g)
        paper_uri = extract_paper_uri(g)
        title = extract_title_from_graph(g)

        data = [[paper_uri], [embedding], [title]]
        collection.insert(data)
    
    print("Collection created")

    index_params = {
        "metric_type":"COSINE",
        "index_type":"FLAT"
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
        "offset": 1, 
        "ignore_growing": False
    }

    g_sim = Graph()
    base = Namespace("https://w3id.org/ocs/ont/papers/")
    g_sim.bind("base", base)

    print("Querying the collection...")

    for ttl_file in file_list:
        print(f"Processing file {os.path.basename(ttl_file)}")

        g = Graph()
        g.parse(os.path.join(ttl_file), format="ttl")

        embedding = extract_embedding_from_graph(g)
        paper_uri = URIRef(extract_paper_uri(g))

    
        results = collection.search(
            data=[embedding], 
            anns_field="embedding_field", 
            param=search_params,
            limit=10,
            expr=None,
            output_fields=['paper_title', 'distance']
        )

        n = 10
        x = [i / (n-1) for i in range(n)]
        y = results[0].distances
        kl = KneeLocator(x, y, curve="concave", direction="decreasing")
        knee = kl.knee

        for res in results[0][knee:10]:

            blank_node = BNode()
            g_sim.add((paper_uri, base.hasRelatedPapers, blank_node))
            
            sim_paper_uri = URIRef(res.id)
            sim_score = res.distance
            
            g_sim.add((blank_node, base.hasOpencsUID, sim_paper_uri))
            g_sim.add((blank_node, base.similarityScore, Literal(sim_score, datatype=XSD.integer)))

    print("Saving results...")

    with open("/home/output/similarity_graph.ttl", "wb") as file:
        g_sim = g_sim.serialize(format="turtle")
        if isinstance(g_sim, str):
            g_sim = g_sim.encode()
        file.write(g_sim)

    for coll in utility.list_collections():
        utility.drop_collection(coll)
    
    if database_name in db.list_database():
        db.drop_database(database_name)

    connections.disconnect(alias="default")

    print("Success")

          
if __name__ == "__main__":
    main()