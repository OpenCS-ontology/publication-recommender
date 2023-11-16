from rdflib import Graph
import os


def list_files(directory):
    file_list = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_list.append(file_path)

    return file_list


def main():

    print("Merging the knowledge graph...")

    directory_path = '/home/input_ttl_files'
    file_list = list_files(directory_path)

    merged_graph = Graph()

    for file in file_list:
        with open(file, "r") as f:
            ttl_content = f.read()
            merged_graph.parse(data=ttl_content, format="turtle")


    with open("/home/output/merged_graph.ttl", "wb") as file:
        merged_graph = merged_graph.serialize(format="turtle")
        if isinstance(merged_graph, str):
            merged_graph = merged_graph.encode()
        file.write(merged_graph)

    print("Graph merged successfully")


if __name__ == "__main__":
    main()
