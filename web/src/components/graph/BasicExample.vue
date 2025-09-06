<script setup lang="ts">
const nodes = {
  node1: { name: "Node 1" },
  node2: { name: "Node 2" },
  node3: { name: "Node 3" },
  node4: { name: "Node 4" },
}

const edges = {
  edge1: { source: "node1", target: "node2" },
  edge2: { source: "node2", target: "node3" },
  edge3: { source: "node3", target: "node4" },
}
</script>

<template>
    <div class="basic-example">
        <h2>Basic Example</h2>
        <p>This is a basic example of a network graph with 4 nodes and 3 edges.</p>
        <v-network-graph :nodes="nodes" :edges="edges" />
    </div>
</template>