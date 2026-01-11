import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from utils import setup_logger, ensure_dir
from agent_detector import AgentDetection

logger = setup_logger("PositionAnalyzer")


@dataclass
class RoundPositions:
    round_num: int
    timestamp: float
    attack: List[Dict]
    defend: List[Dict]
    minimap_file: str


class PositionAnalyzer:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        ensure_dir(self.output_dir)

    def analyze_round(
        self,
        round_num: int,
        timestamp: float,
        minimap_file: str,
        detections: List[AgentDetection],
    ) -> RoundPositions:
        """
        Analyze detected agents and create position data
        """
        # Separate by team
        attack_agents = []
        defend_agents = []

        for det in detections:
            agent_data = {
                "agent": det.agent_name,
                "x": round(det.x, 4),
                "y": round(det.y, 4),
                "confidence": round(det.confidence, 4),
            }

            if det.team == "attack":
                attack_agents.append(agent_data)
            elif det.team == "defend":
                defend_agents.append(agent_data)

        # Sort by confidence
        attack_agents.sort(key=lambda x: x["confidence"], reverse=True)
        defend_agents.sort(key=lambda x: x["confidence"], reverse=True)

        positions = RoundPositions(
            round_num=round_num,
            timestamp=timestamp,
            attack=attack_agents,
            defend=defend_agents,
            minimap_file=minimap_file,
        )

        logger.info(
            f"Round {round_num}: Attack={len(attack_agents)}, Defend={len(defend_agents)}"
        )

        return positions

    def save_positions(self, positions: RoundPositions):
        """
        Save position data to JSON file
        """
        filename = f"round_{positions.round_num:02d}_positions.json"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(positions), f, indent=4, ensure_ascii=False)

        logger.debug(f"Saved positions: {filepath}")

    def load_positions(self, round_num: int) -> Optional[RoundPositions]:
        """
        Load position data from JSON file
        """
        filename = f"round_{round_num:02d}_positions.json"
        filepath = os.path.join(self.output_dir, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return RoundPositions(**data)

    def save_all_positions(self, all_positions: Dict[int, RoundPositions]):
        """
        Save all positions to a single JSON file
        """
        filepath = os.path.join(self.output_dir, "all_positions.json")

        positions_dict = {}
        for round_num, positions in all_positions.items():
            positions_dict[f"round_{round_num:02d}"] = asdict(positions)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(positions_dict, f, indent=4, ensure_ascii=False)

        logger.info(f"Saved all positions to: {filepath}")

    def get_attack_positions(self, round_positions: RoundPositions) -> List[tuple]:
        """
        Get attack positions as (x, y) tuples
        """
        return [(p["x"], p["y"]) for p in round_positions.attack]

    def get_defend_positions(self, round_positions: RoundPositions) -> List[tuple]:
        """
        Get defend positions as (x, y) tuples
        """
        return [(p["x"], p["y"]) for p in round_positions.defend]
