import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, fcluster, dendrogram
from scipy.spatial.distance import cosine
from utils import setup_logger, ensure_dir
from position_analyzer import PositionAnalyzer, RoundPositions

logger = setup_logger("FormationAnalyzer")


class FormationAnalyzer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.position_analyzer = PositionAnalyzer(output_dir)
        ensure_dir(self.output_dir)

    def calculate_centroid(
        self, positions: List[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """
        Calculate centroid of positions
        """
        if not positions:
            return (0.0, 0.0)

        positions = np.array(positions)
        centroid = np.mean(positions, axis=0)
        return tuple(centroid)

    def calculate_distance_matrix(
        self, positions: List[Tuple[float, float]]
    ) -> np.ndarray:
        """
        Calculate pairwise distance matrix
        """
        if len(positions) < 2:
            return np.zeros((1, 1))

        return squareform(pdist(positions, metric="euclidean"))

    def normalize_by_max_distance(self, distance_matrix: np.ndarray) -> np.ndarray:
        """
        Normalize distance matrix by max distance (scale invariant)
        """
        max_dist = np.max(distance_matrix)
        if max_dist == 0:
            return distance_matrix

        return distance_matrix / max_dist

    def upper_triangular_vector(self, matrix: np.ndarray) -> np.ndarray:
        """
        Convert symmetric matrix to upper triangular vector
        """
        n = matrix.shape[0]
        upper = []
        for i in range(n):
            for j in range(i + 1, n):
                upper.append(matrix[i, j])
        return np.array(upper)

    def calculate_formation_similarity(
        self,
        positions1: List[Tuple[float, float]],
        positions2: List[Tuple[float, float]],
    ) -> float:
        """
        Calculate formation similarity using relative positions (rotation and scale invariant)
        """
        if not positions1 or not positions2:
            return 0.0

        # Calculate centroids
        centroid1 = self.calculate_centroid(positions1)
        centroid2 = self.calculate_centroid(positions2)

        # Calculate relative positions from centroid
        rel_pos1 = [(p[0] - centroid1[0], p[1] - centroid1[1]) for p in positions1]
        rel_pos2 = [(p[0] - centroid2[0], p[1] - centroid2[1]) for p in positions2]

        # Calculate distance matrices
        dist_matrix1 = self.calculate_distance_matrix(rel_pos1)
        dist_matrix2 = self.calculate_distance_matrix(rel_pos2)

        # Normalize by max distance (scale invariant)
        norm_matrix1 = self.normalize_by_max_distance(dist_matrix1)
        norm_matrix2 = self.normalize_by_max_distance(dist_matrix2)

        # Convert to upper triangular vectors
        vec1 = self.upper_triangular_vector(norm_matrix1)
        vec2 = self.upper_triangular_vector(norm_matrix2)

        if len(vec1) != len(vec2):
            # Different number of players
            return 0.0

        if len(vec1) == 0:
            return 1.0  # Single player

        # Calculate cosine similarity
        similarity = 1.0 - cosine(vec1, vec2)

        return max(0.0, min(1.0, similarity))

    def calculate_all_similarities(
        self, positions_data: Dict[int, RoundPositions], team: str = "attack"
    ) -> np.ndarray:
        """
        Calculate similarity matrix for all rounds
        """
        round_nums = sorted(positions_data.keys())
        n = len(round_nums)

        if n < 2:
            return np.eye(n)

        similarity_matrix = np.eye(n)

        for i in range(n):
            for j in range(i + 1, n):
                round_i = round_nums[i]
                round_j = round_nums[j]

                pos_i = positions_data[round_i]
                pos_j = positions_data[round_j]

                if team == "attack":
                    positions_i = self.position_analyzer.get_attack_positions(pos_i)
                    positions_j = self.position_analyzer.get_attack_positions(pos_j)
                else:
                    positions_i = self.position_analyzer.get_defend_positions(pos_i)
                    positions_j = self.position_analyzer.get_defend_positions(pos_j)

                similarity = self.calculate_formation_similarity(
                    positions_i, positions_j
                )

                similarity_matrix[i, j] = similarity
                similarity_matrix[j, i] = similarity

        return similarity_matrix

    def cluster_formations(
        self,
        positions_data: Dict[int, RoundPositions],
        similarity_threshold: float = 0.8,
        team: str = "attack",
    ) -> Dict[int, List[int]]:
        """
        Cluster formations based on similarity
        Returns: {cluster_id: [round_numbers]}
        """
        round_nums = sorted(positions_data.keys())
        n = len(round_nums)

        if n < 2:
            return {0: round_nums}

        # Calculate similarity matrix
        similarity_matrix = self.calculate_all_similarities(positions_data, team)

        # Convert to distance matrix
        distance_matrix = 1.0 - similarity_matrix

        # Hierarchical clustering
        Z = linkage(squareform(distance_matrix), method="complete")

        # Cut tree at threshold
        cluster_labels = fcluster(Z, t=1.0 - similarity_threshold, criterion="distance")

        # Group rounds by cluster
        clusters: Dict[int, List[int]] = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(round_nums[i])

        # Sort clusters by size (largest first)
        clusters = dict(sorted(clusters.items(), key=lambda x: -len(x[1])))

        # Reassign cluster IDs starting from 0
        sorted_clusters = {}
        for new_id, (old_id, rounds) in enumerate(clusters.items()):
            sorted_clusters[new_id] = rounds

        logger.info(f"Clustered into {len(sorted_clusters)} groups using {team} team")
        for cluster_id, rounds in sorted_clusters.items():
            logger.info(f"  Cluster {cluster_id}: {rounds}")

        return sorted_clusters

    def name_cluster(
        self,
        cluster_id: int,
        rounds: List[int],
        positions_data: Dict[int, RoundPositions],
        team: str = "attack",
    ) -> str:
        """
        Generate a descriptive name for the cluster
        """
        # Calculate average centroid for the cluster
        centroids = []

        for round_num in rounds:
            pos = positions_data[round_num]
            if team == "attack":
                positions = self.position_analyzer.get_attack_positions(pos)
            else:
                positions = self.position_analyzer.get_defend_positions(pos)

            centroid = self.calculate_centroid(positions)
            centroids.append(centroid)

        if not centroids:
            return f"Formation {cluster_id}"

        avg_centroid = np.mean(centroids, axis=0)

        # Simple naming based on position
        x, y = avg_centroid

        if x < 0.4:
            position_name = "Left side"
        elif x > 0.6:
            position_name = "Right side"
        else:
            position_name = "Mid/Center"

        if y < 0.4:
            position_name += " - Top"
        elif y > 0.6:
            position_name += " - Bottom"

        return f"{position_name} setup"

    def save_clusters(
        self,
        clusters: Dict[int, List[int]],
        cluster_names: Dict[int, str],
        positions_data: Dict[int, RoundPositions],
    ):
        """
        Save clustering results to JSON
        """
        filepath = os.path.join(self.output_dir, "formation_analysis.json")

        result = {"clusters": []}

        for cluster_id, rounds in clusters.items():
            cluster_data = {
                "id": cluster_id,
                "name": cluster_names.get(cluster_id, f"Formation {cluster_id}"),
                "rounds": rounds,
            }
            result["clusters"].append(cluster_data)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        logger.info(f"Saved formation analysis to: {filepath}")
