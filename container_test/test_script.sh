cp /home/container_test/test_recommender/* /home/input_ttl_files
mkdir -p /home/output/
python3 /home/similar_papers.py
python3 /home/merge_graphs.py