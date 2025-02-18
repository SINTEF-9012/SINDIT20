# Step 1: Use the official GraphDB base image
FROM ontotext/graphdb:10.2.2-arm64

RUN apt-get update
RUN apt-get --assume-yes install curl

# Step 2: Set the working directory to the GraphDB home directory (where GraphDB stores repositories)
WORKDIR /opt/graphdb/home

# Step 3: Copy the local GraphDB home directory (containing the indexed repository) to the container
# Replace '/path/to/GraphDB/home' with the path to your local GraphDB home directory
COPY . /opt/graphdb/home/

ENV GDB_JAVA_OPTS="-Xms2g -Xmx4g"

RUN mkdir -p tmp
RUN importrdf preload --force --recursive -q .tmp/ -c ./repo-config.ttl ./graph_model
RUN rm -rf ./tmp

# Step 4: Expose the necessary ports (GraphDB runs on port 7200 by default)
EXPOSE 7200

# Step 5: Start the GraphDB server
CMD ["../bin/graphdb"]
