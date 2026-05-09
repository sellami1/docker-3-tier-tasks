"""
K3s Kubernetes — 3-Tier Tasks Application (namespace: tasks-app)

Requires:
    pip install diagrams
    apt install graphviz   # or: brew install graphviz

Run:
    python k3s_tasks_architecture.py
Output:
    k3s_tasks_architecture.png  (same directory as this script)
"""

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.onprem.network import Nginx, Traefik
from diagrams.onprem.database import MongoDB
from diagrams.programming.language import NodeJS
from diagrams.programming.framework import React
from diagrams.k8s.compute import Deployment, Pod, StatefulSet
from diagrams.k8s.network import Ing, SVC
from diagrams.k8s.storage import PVC, SC
from diagrams.k8s.podconfig import CM, Secret
from diagrams.k8s.clusterconfig import HPA

# ── output ───────────────────────────────────────────────────────────────────
OUTPUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "k3s_tasks_architecture",
)

# ── graph styling ─────────────────────────────────────────────────────────────
GRAPH_ATTR = {
    "fontsize": "14",
    "bgcolor": "white",
    "pad": "0.75",
    "splines": "ortho",
    "nodesep": "0.6",
    "ranksep": "1.4",
    "rankdir": "LR",
}

# cluster styles
K3S_CLUSTER = {
    "bgcolor": "#EEF4FB",
    "pencolor": "#2E6DA4",
    "fontcolor": "#2E6DA4",
    "style": "rounded",
    "fontsize": "13",
}
NS_CLUSTER = {
    "bgcolor": "#F5F5F5",
    "pencolor": "#555555",
    "fontcolor": "#333333",
    "style": "dashed",
    "fontsize": "12",
}
TIER_FRONTEND = {
    "bgcolor": "#EAF4FF",
    "pencolor": "#4A90D9",
    "fontcolor": "#4A90D9",
    "style": "dashed",
    "fontsize": "11",
}
TIER_BACKEND = {
    "bgcolor": "#FFF8EC",
    "pencolor": "#E8A020",
    "fontcolor": "#C07010",
    "style": "dashed",
    "fontsize": "11",
}
TIER_DATABASE = {
    "bgcolor": "#F0FFF0",
    "pencolor": "#3A8C3A",
    "fontcolor": "#2A6C2A",
    "style": "dashed",
    "fontsize": "11",
}
NETPOL_CLUSTER = {
    "bgcolor": "transparent",
    "pencolor": "#CC0000",
    "fontcolor": "#CC0000",
    "style": "dotted",
    "fontsize": "10",
}
STORAGE_CLUSTER = {
    "bgcolor": "#FDF6FF",
    "pencolor": "#9B59B6",
    "fontcolor": "#7D3C98",
    "style": "dashed",
    "fontsize": "11",
}
CONFIG_CLUSTER = {
    "bgcolor": "#FAFAFA",
    "pencolor": "#888888",
    "fontcolor": "#555555",
    "style": "dotted",
    "fontsize": "10",
}

# ── edge helpers ──────────────────────────────────────────────────────────────
def traffic(label=""):
    return Edge(label=label, color="#2E6DA4", style="bold")

def svc_edge(label=""):
    return Edge(label=label, color="#555555", style="solid")

def config_edge():
    return Edge(color="#888888", style="dashed", arrowhead="open")

def netpol_edge():
    return Edge(color="#CC0000", style="dotted", arrowhead="none")

def storage_edge(label=""):
    return Edge(label=label, color="#9B59B6", style="dashed")

def hpa_edge():
    return Edge(color="#E8A020", style="dashed", label="scales 2–5\n@ CPU 70%")


# ─────────────────────────────────────────────────────────────────────────────
with Diagram(
    "K3s — Tasks App (namespace: tasks-app)",
    filename=OUTPUT,
    show=False,
    direction="LR",
    graph_attr=GRAPH_ATTR,
):

    # ── External ──────────────────────────────────────────────────────────────
    browser = Users("Browser\n(end-user)")

    # ── K3s cluster ───────────────────────────────────────────────────────────
    with Cluster("K3s Cluster", graph_attr=K3S_CLUSTER):

        # NodePort entry point (outside namespace but inside cluster)
        nodeport_svc = SVC("frontend-nodeport\nNodePort :30080")

        # ── Namespace: tasks-app ─────────────────────────────────────────────
        with Cluster("namespace: tasks-app", graph_attr=NS_CLUSTER):

            # ── Ingress ───────────────────────────────────────────────────────
            traefik_ing = Traefik(
                "tasks-ingress\nTraefik Ingress\ntasks.local → frontend:80"
            )

            # ── Shared ConfigMap / Secret (referenced by multiple tiers) ──────
            with Cluster("Shared Config & Secrets", graph_attr=CONFIG_CLUSTER):
                app_config = CM("app-config\nDB_HOST · DB_PORT · DB_NAME\nPORT · ORIGIN")
                db_secrets = Secret("db-secrets\nDB_ROOT_USER/PW\nDB_APP_USER/PW")

            # ── FRONTEND TIER ─────────────────────────────────────────────────
            with Cluster(
                "Frontend Tier\nNetworkPolicy: allow 0.0.0.0/0 → TCP 80",
                graph_attr={**TIER_FRONTEND, **NETPOL_CLUSTER, "pencolor": "#CC0000"},
            ):
                fe_svc = SVC("frontend\nClusterIP :80")
                fe_deploy = Deployment(
                    "frontend  (Deployment)\n2 replicas · RollingUpdate\nmaxSurge:1 · maxUnavail:0"
                )
                fe_pod_1 = Pod("frontend-pod-1\nnginx:alpine\nReact SPA :80\nuser 1001")
                fe_pod_2 = Pod("frontend-pod-2\nnginx:alpine\nReact SPA :80\nuser 1001")
                fe_config = CM("frontend-config\nVITE_API_URL")

            # ── BACKEND TIER ──────────────────────────────────────────────────
            with Cluster(
                "Backend Tier\nNetworkPolicy: allow frontend → TCP 3000",
                graph_attr={**TIER_BACKEND, **NETPOL_CLUSTER, "pencolor": "#CC0000"},
            ):
                be_svc = SVC("backend\nClusterIP :3000")
                be_deploy = Deployment(
                    "backend  (Deployment)\n2 replicas · RollingUpdate"
                )
                be_pod_1 = Pod("backend-pod-1\nNode.js/Express :3000\nuser 1001")
                be_pod_2 = Pod("backend-pod-2\nNode.js/Express :3000\nuser 1001")
                be_hpa = HPA(
                    "backend-hpa\nHPA 2–5 replicas\nCPU target 70%"
                )

            # ── DATABASE TIER ─────────────────────────────────────────────────
            with Cluster(
                "Database Tier\nNetworkPolicy: allow backend → TCP 27017",
                graph_attr={**TIER_DATABASE, **NETPOL_CLUSTER, "pencolor": "#CC0000"},
            ):
                db_svc = SVC("database\nClusterIP :27017")
                db_headless = SVC("database-headless\nHeadless (clusterIP: None)")
                db_ss = StatefulSet(
                    "database  (StatefulSet)\n1 replica\nmongo:7.0 :27017\nuser 999"
                )
                db_pod = Pod("database-pod-0\nmongo:7.0\nping probe via mongosh")
                mongo_init = CM("mongo-init-script\nmounted as init script")

            # ── STORAGE ───────────────────────────────────────────────────────
            with Cluster("Storage", graph_attr=STORAGE_CLUSTER):
                pvc = PVC("mongo-data (PVC)\nmounted at /data/db")
                sc = SC(
                    "app-local-path (StorageClass)\nprovisioner: rancher.io/local-path\n"
                    "reclaimPolicy: Retain\nbindingMode: WaitForFirstConsumer"
                )

    # ── Edge wiring ───────────────────────────────────────────────────────────

    # External → Ingress / NodePort
    browser >> traffic("tasks.local\nHTTP") >> traefik_ing
    browser >> traffic(":30080\nNodePort") >> nodeport_svc

    # Ingress & NodePort → frontend service
    traefik_ing >> svc_edge("→ frontend:80") >> fe_svc
    nodeport_svc >> svc_edge() >> fe_svc

    # Frontend service → pods (load-balanced)
    fe_svc >> svc_edge() >> fe_pod_1
    fe_svc >> svc_edge() >> fe_pod_2

    # Deployment manages pods
    fe_deploy >> Edge(style="dotted", color="#4A90D9") >> fe_pod_1
    fe_deploy >> Edge(style="dotted", color="#4A90D9") >> fe_pod_2

    # Frontend config injection
    fe_config >> config_edge() >> fe_pod_1
    fe_config >> config_edge() >> fe_pod_2
    app_config >> config_edge() >> fe_pod_1
    app_config >> config_edge() >> fe_pod_2

    # Frontend pods → backend service
    fe_pod_1 >> traffic("API calls\n→ :3000") >> be_svc
    fe_pod_2 >> traffic() >> be_svc

    # Backend service → pods
    be_svc >> svc_edge() >> be_pod_1
    be_svc >> svc_edge() >> be_pod_2

    # Deployment manages pods
    be_deploy >> Edge(style="dotted", color="#E8A020") >> be_pod_1
    be_deploy >> Edge(style="dotted", color="#E8A020") >> be_pod_2

    # HPA → backend deployment
    be_hpa >> hpa_edge() >> be_deploy

    # Backend config & secrets
    app_config >> config_edge() >> be_pod_1
    app_config >> config_edge() >> be_pod_2
    db_secrets >> config_edge() >> be_pod_1
    db_secrets >> config_edge() >> be_pod_2

    # Backend pods → database service
    be_pod_1 >> traffic("→ :27017") >> db_svc
    be_pod_2 >> traffic() >> db_svc

    # DB services → pod
    db_svc >> svc_edge() >> db_pod
    db_headless >> svc_edge("pod identity") >> db_pod

    # StatefulSet manages pod
    db_ss >> Edge(style="dotted", color="#3A8C3A") >> db_pod

    # DB config & secrets
    app_config >> config_edge() >> db_pod
    db_secrets >> config_edge() >> db_pod
    mongo_init >> config_edge() >> db_pod

    # Storage wiring
    pvc >> storage_edge("/data/db") >> db_pod
    sc >> storage_edge("provisions") >> pvc