###### Checklist_Best_Practices-Projet_DevOps.md

# Checklist des Best Practices - Projet DevOps

À cocher par l’étudiant avant le rendu du projet (Docker Compose + Kubernetes K3s)

## Phase 1 : Docker Compose

- [ ] Utilisation d’un fichier `compose.yaml` moderne
- [ ] Multi-stage builds dans les Dockerfiles (frontend et backend)
- [ ] Healthchecks définis pour chaque service
- [ ] `depends_on` avec `condition: service_healthy`
- [ ] Réseaux personnalisés (`networks`)
- [ ] Volumes nommés pour la persistance des données (surtout DB)
- [ ] Fichier `.env` + exclusion via `.gitignore` et `.dockerignore`
- [ ] Gestion correcte des secrets et variables sensibles
- [ ] `restart: unless-stopped` pour les services critiques
- [ ] Utilisateur non-root (`user:`) dans les conteneurs
- [ ] Logging configuré avec limite de taille
- [ ] Images avec tags explicites (éviter `latest` en production)
- [ ] Profils ou fichiers overrides pour séparer dev/prod

## Phase 2 : Kubernetes (K3s)

- [ ] Namespace dédié pour l’application
- [ ] Structure claire des manifests dans Git (`deployments/`, `services/`, `configmaps/`, `secrets/`, etc.)
- [ ] Labels et selectors cohérents et significatifs

### Deployments :
- [ ] 3 Deployments distincts (ou StatefulSet pour la DB)
- [ ] Resource requests et limits définis sur tous les conteneurs
- [ ] Liveness Probe et Readiness Probe configurées
- [ ] Stratégie de déploiement RollingUpdate bien paramétrée
- [ ] Conteneurs exécutés en non-root (`securityContext`)
- [ ] Nombre de replicas ≥ 2 pour les services critiques

### Services & Exposition :
- [ ] Services ClusterIP pour backend et base de données
- [ ] Service pour exposer le frontend (NodePort / LoadBalancer ou Ingress)
- [ ] ConfigMaps pour les configurations non sensibles
- [ ] Secrets pour tous les éléments sensibles
- [ ] Secrets montés en volume ou en variables d’environnement de manière sécurisée

### Stockage :
- [ ] PVC créé pour la persistance de la base de données
- [ ] StorageClass adaptée (`local-path` dans K3s)

### Tests, Résilience & Bonus

- [ ] Application fonctionnelle sur Docker Compose
- [ ] Application fonctionnelle et accessible sur le cluster K3s
- [ ] Test de résilience (suppression d’un pod ou d’un worker)
- [ ] Logs et diagnostic accessibles via `kubectl`
- [ ] Bonus : Utilisation d’Ingress
- [ ] Bonus : Horizontal Pod Autoscaler (HPA)
- [ ] Bonus : StatefulSet pour la base de données
- [ ] Bonus : NetworkPolicy
- [ ] Bonus : Monitoring basique (Prometheus/Grafana)

**Recommandation** : Cette checklist doit être remplie et jointe au rapport DOCX. Elle permet à l’enseignant d’évaluer rapidement la qualité technique de votre travail.