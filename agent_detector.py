import cv2
import numpy as np
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from utils import setup_logger

logger = setup_logger("AgentDetector")


@dataclass
class AgentDetection:
    agent_name: str
    x: float  # Normalized x (0-1)
    y: float  # Normalized y (0-1)
    team: str  # "attack" or "defend"
    confidence: float
    pixel_x: int
    pixel_y: int


class AgentDetector:
    def __init__(
        self,
        icons_dir: str = "valorant_agent_icons",
        detection_threshold: float = 0.7,
        nms_iou_threshold: float = 0.3,
        team_color_offset: int = 40,
    ):
        self.icons_dir = icons_dir
        self.detection_threshold = detection_threshold
        self.nms_iou_threshold = nms_iou_threshold
        self.team_color_offset = team_color_offset

        # Scale variations for template matching
        self.scales = [64, 48, 32]

        self.agent_templates = self._load_agent_templates()
        self.agent_names = list(self.agent_templates.keys())
        logger.info(f"Loaded {len(self.agent_names)} agent templates")

    def _load_agent_templates(self) -> Dict[str, List[np.ndarray]]:
        """
        Load all agent icon templates with alpha channel
        Returns: {agent_name: [template_64, template_48, template_32]}
        """
        templates = {}

        if not os.path.exists(self.icons_dir):
            logger.error(f"Icons directory not found: {self.icons_dir}")
            return templates

        for filename in sorted(os.listdir(self.icons_dir)):
            if not filename.endswith(".png"):
                continue

            agent_name = filename.replace(".png", "")
            filepath = os.path.join(self.icons_dir, filename)

            # Load with alpha channel
            template = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)

            if template is None:
                logger.warning(f"Failed to load: {filename}")
                continue

            # Create templates at different scales
            scaled_templates = []
            for scale in self.scales:
                # Resize maintaining aspect ratio
                h, w = template.shape[:2]
                if h > w:
                    new_h = scale
                    new_w = int(w * scale / h)
                else:
                    new_w = scale
                    new_h = int(h * scale / w)

                scaled = cv2.resize(
                    template, (new_w, new_h), interpolation=cv2.INTER_AREA
                )
                scaled_templates.append(scaled)

            templates[agent_name] = scaled_templates
            logger.debug(f"Loaded {agent_name}: {[t.shape for t in scaled_templates]}")

        return templates

    def _classify_team(
        self, image: np.ndarray, x: int, y: int, template_size: Tuple[int, int]
    ) -> str:
        """
        Classify team based on color around the detection
        Red circle = attack, Blue/Green circle = defend
        """
        h, w = image.shape[:2]
        tw, th = template_size

        # Sample colors in a ring around the detection (outside the template)
        ring_width = 5
        radius = max(tw, th) // 2 + ring_width

        # Define sampling region (clamped to image bounds)
        y_min = max(0, y - radius)
        y_max = min(h, y + radius)
        x_min = max(0, x - radius)
        x_max = min(w, x + radius)

        region = image[y_min:y_max, x_min:x_max]

        if region.size == 0:
            return "unknown"

        # Convert to RGB
        region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)

        # Sample pixels in the ring
        mask_radius = max(tw, th) // 2
        center_y, center_x = y - y_min, x - x_min
        yy, xx = np.ogrid[: region.shape[0], : region.shape[1]]
        distance = np.sqrt((xx - center_x) ** 2 + (yy - center_y) ** 2)
        ring_mask = (distance >= mask_radius) & (distance <= radius)

        ring_pixels = region_rgb[ring_mask]

        if len(ring_pixels) < 10:
            return "unknown"

        # Calculate average color
        avg_color = np.mean(ring_pixels, axis=0)
        r, g, b = avg_color

        offset = self.team_color_offset

        # Red = attack
        if r > g + offset and r > b + offset:
            return "attack"
        # Blue or Green = defend
        elif b > r + offset or g > r + offset:
            return "defend"
        else:
            # Check which color is dominant
            if r >= g and r >= b:
                return "attack"
            else:
                return "defend"

    def _non_max_suppression(
        self, detections: List[Dict], iou_threshold: float
    ) -> List[Dict]:
        """
        NMS to remove duplicate detections
        """
        if not detections:
            return []

        # Sort by confidence
        detections.sort(key=lambda x: x["confidence"], reverse=True)

        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)

            # Remove detections with high IoU
            remaining = []
            for det in detections:
                iou = self._calculate_iou(best, det)
                if iou < iou_threshold:
                    remaining.append(det)
            detections = remaining

        return keep

    def _calculate_iou(self, det1: Dict, det2: Dict) -> float:
        """
        Calculate IoU between two detections
        """
        x1, y1, w1, h1 = (
            det1["x"] - det1["w"] // 2,
            det1["y"] - det1["h"] // 2,
            det1["w"],
            det1["h"],
        )
        x2, y2, w2, h2 = (
            det2["x"] - det2["w"] // 2,
            det2["y"] - det2["h"] // 2,
            det2["w"],
            det2["h"],
        )

        # Intersection
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)

        inter_w = max(0, xi2 - xi1)
        inter_h = max(0, yi2 - yi1)
        inter_area = inter_w * inter_h

        # Union
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - inter_area

        if union_area == 0:
            return 0

        return inter_area / union_area

    def _remove_duplicate_agents_by_team(
        self, detections: List[AgentDetection]
    ) -> List[AgentDetection]:
        """
        Remove duplicate agents within each team.
        In Valorant, the same agent cannot appear twice on the same team.
        Keep only the detection with highest confidence for each (team, agent) pair.
        """
        # Group by (team, agent_name)
        team_agent_groups: Dict[Tuple[str, str], List[AgentDetection]] = {}

        for det in detections:
            key = (det.team, det.agent_name)
            if key not in team_agent_groups:
                team_agent_groups[key] = []
            team_agent_groups[key].append(det)

        # Keep only the highest confidence detection for each group
        filtered_detections = []
        for key, group in team_agent_groups.items():
            if len(group) > 1:
                # Sort by confidence descending and keep the best
                group.sort(key=lambda x: x.confidence, reverse=True)
                filtered_detections.append(group[0])
                logger.debug(
                    f"Removed duplicate {key[0]} agent {key[1]} (kept confidence: {group[0].confidence:.3f})"
                )
            else:
                filtered_detections.append(group[0])

        return filtered_detections

    def detect(self, minimap: np.ndarray) -> List[AgentDetection]:
        """
        Detect agents on minimap
        Returns: List of AgentDetection
        """
        if minimap is None or minimap.size == 0:
            logger.warning("Empty minimap image")
            return []

        h, w = minimap.shape[:2]
        all_detections = []

        # Match each agent template at different scales
        for agent_name, templates in self.agent_templates.items():
            for template in templates:
                th, tw = template.shape[:2]

                # Handle alpha channel - use it as mask
                if template.shape[2] == 4:
                    alpha = template[:, :, 3] / 255.0
                    template_rgb = template[:, :, :3]
                else:
                    alpha = None
                    template_rgb = template

                # Template matching
                if alpha is not None:
                    # Weighted template matching with alpha mask
                    result = np.zeros((h - th + 1, w - tw + 1), dtype=np.float32)
                    for c in range(3):
                        channel_result = cv2.matchTemplate(
                            minimap[:, :, c].astype(np.float32),
                            (template_rgb[:, :, c] * alpha).astype(np.float32),
                            cv2.TM_CCOEFF_NORMED,
                        )
                        result += channel_result
                    result /= 3
                else:
                    results = []
                    for c in range(3):
                        channel_result = cv2.matchTemplate(
                            minimap[:, :, c].astype(np.float32),
                            template_rgb[:, :, c].astype(np.float32),
                            cv2.TM_CCOEFF_NORMED,
                        )
                        results.append(channel_result)
                    result = sum(results) / len(results)

                # Get all locations above threshold
                locs = np.where(result >= self.detection_threshold)

                for pt in zip(*locs[::-1]):
                    all_detections.append(
                        {
                            "agent_name": agent_name,
                            "x": pt[0] + tw // 2,
                            "y": pt[1] + th // 2,
                            "w": tw,
                            "h": th,
                            "confidence": float(result[pt[1], pt[0]]),
                        }
                    )

        # NMS to remove duplicates (same agent at nearby positions)
        filtered_detections = self._non_max_suppression(
            all_detections, self.nms_iou_threshold
        )

        # Classify team and create AgentDetection objects
        agent_detections = []
        for det in filtered_detections:
            team = self._classify_team(
                minimap, det["x"], det["y"], (det["w"], det["h"])
            )

            # Normalize coordinates
            norm_x = det["x"] / w
            norm_y = det["y"] / h

            detection = AgentDetection(
                agent_name=det["agent_name"],
                x=norm_x,
                y=norm_y,
                team=team,
                confidence=det["confidence"],
                pixel_x=det["x"],
                pixel_y=det["y"],
            )
            agent_detections.append(detection)

        # Remove duplicate agents within each team (same agent cannot be used twice)
        agent_detections = self._remove_duplicate_agents_by_team(agent_detections)

        # Limit to top 5 agents per team (max team size in Valorant)
        agent_detections = self._limit_team_size(agent_detections)

        logger.info(
            f"Detected {len(agent_detections)} agents: {self._count_by_team(agent_detections)}"
        )

        return agent_detections

    def _limit_team_size(
        self, detections: List[AgentDetection], max_per_team: int = 5
    ) -> List[AgentDetection]:
        """
        Limit detections to top N agents per team based on confidence.
        """
        # Separate by team
        attack = [d for d in detections if d.team == "attack"]
        defend = [d for d in detections if d.team == "defend"]

        # Sort by confidence and keep top N
        attack.sort(key=lambda x: x.confidence, reverse=True)
        defend.sort(key=lambda x: x.confidence, reverse=True)

        final_detections = attack[:max_per_team] + defend[:max_per_team]

        return final_detections

    def _count_by_team(self, detections: List[AgentDetection]) -> Dict[str, int]:
        count = {}
        for det in detections:
            team = det.team
            count[team] = count.get(team, 0) + 1
        return count
