from rdflib import *
import os
import tqdm


def list_files(directory):
    file_list = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)

    return file_list


def divide_into_subgraph(graph, s, p, o,
                          papers, articles, conf_papers, authors, organizations, bibliography,
                            fabio, schema, doco, deo, pro, frapo, co, datacite, literal, ocs_papers):
    
    if ((s, RDF.type, fabio.ResearchPaper) in graph) or ((s, RDF.type, ocs_papers.RelatedTopicRelation) in graph):
        papers.add((s, p, o))
        return
    
    for article_object in ['JournalArticle', 'JournalIssue', 'JournalVolume', 'Journal']:
        if (s, RDF.type, URIRef(fabio + article_object)) in graph:
            articles.add((s, p, o))
            return

    for conference_object in ['ConferencePaper', 'ConferenceProceedings']:  
        if (s, RDF.type, URIRef(fabio + conference_object)) in graph:
            conf_papers.add((s, p, o))
            return

    if (((s, RDF.type, schema.Person) in graph) and ("author" in str(s))) or ((s, RDF.type, pro.RoleInTime) in graph):
        authors.add((s, p, o))
        return

    if (s, RDF.type, frapo.Organization) in graph:
        organizations.add((s, p, o))
        return
    
    stype = graph.value(subject=s, predicate=RDF.type)
    if stype:
        if (any(namespace in stype for namespace in [doco, deo])):
            bibliography.add((s,p,o))
            return
        
    if (p.startswith(co)):
        bibliography.add((s,p,o))
        return
    
    if p == URIRef(datacite + "hasDescriptionType") or p == URIRef(literal + "hasLiteralValue"):
        papers.add((s, p, o))
        return
    
    if "BIBREF" in str(s):
        bibliography.add((s,p,o))
        return

    bibliography.add((s, p, o))
    return

def main():

    print("Creating the knowledge graph...")

    directory_path = '/home/input_ttl_files'
    file_list = list_files(directory_path)
    assert file_list

    cs_kg = Namespace("https://w3id.org/ocs/kg/papers/")
    ocs_papers = Namespace("https://w3id.org/ocs/ont/papers/")
    datacite = Namespace("http://purl.org/spar/datacite/")
    dc = Namespace("http://purl.org/dc/terms/")
    fabio = Namespace("http://purl.org/spar/fabio/")
    frapo = Namespace("http://purl.org/cerif/frapo/")
    frbr = Namespace("http://purl.org/vocab/frbr/core#")
    literal = Namespace("http://www.essepuntato.it/2010/06/literalreification/")
    prism = Namespace("http://prismstandard.org/namespaces/basic/2.0/")
    pro = Namespace("http://purl.org/spar/pro/")
    schema = Namespace("http://schema.org/")
    owl = Namespace("http://www.w3.org/2002/07/owl#")
    c4o = Namespace("http://purl.org/spar/c4o/")
    co = Namespace("http://purl.org/co/")
    deo = Namespace("http://purl.org/spar/deo/")
    doco = Namespace("http://purl.org/spar/doco/")
    po = Namespace("http://www.essepuntato.it/2008/12/pattern#")
    xsd = Namespace("http://www.w3.org/2001/XMLSchema#")

    dir = "/home/output/knowledge_graph/"
    if not os.path.exists(dir):
        os.mkdir(dir)

    articles_file = dir + "articles.ttl"
    authors_file = dir + "authors.ttl"
    bibliography_file = dir + "bibliography.ttl"
    conf_papers_file = dir + "conf_papers.ttl"
    papers_file = dir + "papers.ttl"
    organizations_file = dir + "organizations.ttl"


    articles = Graph()
    authors = Graph()
    bibliography = Graph()
    conf_papers = Graph()
    papers = Graph()
    organizations = Graph()

    graphs = [articles, authors, bibliography, conf_papers, papers, organizations]

    for gr in graphs:
        gr.bind("ocs_papers", ocs_papers)
        gr.bind("", cs_kg)
        gr.bind("datacite", datacite)
        gr.bind("dc", dc)
        gr.bind("fabio", fabio)
        gr.bind("frapo", frapo)
        gr.bind("frbr", frbr)
        gr.bind("literal", literal)
        gr.bind("prism", prism)
        gr.bind("pro", pro)
        gr.bind("schema", schema)
        gr.bind("owl", owl)
        gr.bind("c4o", c4o)
        gr.bind("co", co)
        gr.bind("deo", deo)
        gr.bind("doco", doco)
        gr.bind("po", po)
        gr.bind("xsd", xsd)


    for file in tqdm.tqdm(file_list, total=len(file_list)):
        graph = Graph()
        
        graph.bind("ocs_papers", ocs_papers)
        graph.bind("", cs_kg)
        graph.bind("datacite", datacite)
        graph.bind("dc", dc)
        graph.bind("fabio", fabio)
        graph.bind("frapo", frapo)
        graph.bind("frbr", frbr)
        graph.bind("literal", literal)
        graph.bind("prism", prism)
        graph.bind("pro", pro)
        graph.bind("schema", schema)
        graph.bind("owl", owl)
        graph.bind("c4o", c4o)
        graph.bind("co", co)
        graph.bind("deo", deo)
        graph.bind("doco", doco)
        graph.bind("po", po)
        graph.bind("xsd", xsd)

        with open(file, "r") as f:
            ttl_content = f.read()
            assert ttl_content

            graph.parse(data=ttl_content, format="turtle")

            for s, p, o in graph.triples((None, None, None)):
                divide_into_subgraph(graph, s, p, o,
                                      papers, articles, conf_papers, authors, organizations, bibliography,
                                        fabio, schema, doco, deo, pro, frapo, co, datacite, literal, ocs_papers)


    with open(articles_file, "wb") as file:
        g = articles.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)
    with open(authors_file, "wb") as file:
        g = authors.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)
    with open(bibliography_file, "wb") as file:
        g = bibliography.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)
    with open(conf_papers_file, "wb") as file:
        g = conf_papers.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)
    with open(papers_file, "wb") as file:
        g = papers.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)
    with open(organizations_file, "wb") as file:
        g = organizations.serialize(format='turtle')
        if isinstance(g, str):
            g = g.encode()
        file.write(g)

    print("Graph created successfully")


if __name__ == "__main__":
    main()
