"""
Docker Compose 3-tier architecture diagram.

Requires:
    pip install diagrams
    # plus Graphviz system package:  apt install graphviz  /  brew install graphviz

Run:
    python docker_compose_architecture.py
Output:
    docker_compose_architecture.png  (written next to this script)
"""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users          # browser / end-user
from diagrams.onprem.network import Nginx
from diagrams.onprem.database import MongoDB
from diagrams.programming.language import NodeJS
from diagrams.programming.framework import React
# Volume icon replaced with MongoDB

# ── output path: same directory as this script ──────────────────────────────
OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "docker_compose_architecture")

GRAPH_ATTR = {
    "fontsize": "13",
    "bgcolor": "white",
    "pad": "0.6",
    "splines": "ortho",
    "nodesep": "0.8",
    "ranksep": "1.2",
}

CLUSTER_FRONTEND_NET = {
    "style": "dashed",
    "bgcolor": "aliceblue",
    "pencolor": "#4A90D9",
    "fontcolor": "#4A90D9",
    "fontsize": "11",
}

CLUSTER_BACKEND_NET = {
    "style": "dashed",
    "bgcolor": "#FFF8E7",
    "pencolor": "#E8A020",
    "fontcolor": "#E8A020",
    "fontsize": "11",
}

with Diagram(
    "Docker Compose — 3-Tier Architecture",
    filename=OUTPUT,
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
):
    # ── External user ────────────────────────────────────────────────────────
    user = Users("Browser\n(end-user)")

    # ── frontend-net cluster (frontend + backend share this network) ─────────
    with Cluster("frontend-net  [bridge]", graph_attr=CLUSTER_FRONTEND_NET):

        # frontend service
        with Cluster(
            "frontend  (mem 128 m · cpu 0.25)\n"
            "nginx:alpine · port 8080\n"
            "healthcheck /\n"
            "multi-stage: node:20-alpine → nginx:alpine\n"
            "build-arg VITE_API_URL",
        ):
            nginx = Nginx("Nginx\n:8080")
            react = React("React SPA\n(Vite build)")

        # backend service sits in BOTH networks; represent it once here
        with Cluster(
            "backend  (mem 256 m · cpu 0.5)\n"
            "node:20-alpine · port 3000\n"
            "healthcheck /health  ·  depends_on: db healthy\n"
            "multi-stage: builder → runner",
        ):
            backend = NodeJS("Express / Node.js\n:3000")

    # ── backend-net cluster (backend + database only) ────────────────────────
    with Cluster("backend-net  [bridge]", graph_attr=CLUSTER_BACKEND_NET):

        # database service
        with Cluster(
            "database  (mem 512 m · cpu 0.5)\n"
            "mongo:7.0\n"
            "healthcheck via mongosh\n"
            "initdb script mounted",
        ):
            mongo = MongoDB("MongoDB 7.0")

        # Named volume attached to MongoDB
        mongo_vol = MongoDB("mongo-data\n(named volume)")

    # ── Edges ────────────────────────────────────────────────────────────────

    # 1. User → Nginx (host port 8080)
    user >> Edge(label="HTTP :8080", color="#4A90D9") >> nginx

    # 2. Nginx serves static React assets
    nginx >> Edge(label="serves static\nassets", style="dashed", color="#4A90D9") >> react

    # 3. Nginx proxies API calls to backend
    nginx >> Edge(label="proxy /api/*\n→ :3000", color="#4A90D9") >> backend

    # 4. Backend → MongoDB
    backend >> Edge(label="MongoDB driver\n:27017", color="#E8A020") >> mongo

    # 5. Named volume → MongoDB
    mongo_vol >> Edge(label="mount\n/data/db", style="dotted", color="#888888") >> mongo