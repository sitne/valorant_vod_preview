import os
from typing import Dict, List, Optional
from datetime import datetime
from utils import setup_logger
from position_analyzer import RoundPositions
from formation_analyzer import FormationAnalyzer

logger = setup_logger("ReportGenerator")


class ReportGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir

    def generate_markdown(
        self,
        positions_data: Dict[int, RoundPositions],
        clusters: Optional[Dict[int, List[int]]] = None,
        cluster_names: Optional[Dict[int, str]] = None,
        video_file: Optional[str] = None,
    ) -> str:
        """
        Generate markdown scouting report
        """
        lines = []

        # Title and metadata
        lines.append("# スカウティングレポート")
        lines.append("")
        lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if video_file:
            lines.append(f"ビデオ: {os.path.basename(video_file)}")
        lines.append(f"総ラウンド数: {len(positions_data)}")
        lines.append("")

        # Formation clusters section
        if clusters and cluster_names:
            lines.append("---")
            lines.append("")
            lines.append("## 配置類似グループ")
            lines.append("")

            for cluster_id, rounds in clusters.items():
                cluster_name = cluster_names.get(cluster_id, f"Formation {cluster_id}")

                # Calculate average similarity
                if len(rounds) > 1:
                    # Simplified calculation
                    avg_similarity = "未計算"
                else:
                    avg_similarity = "-"

                lines.append(f"### 🎯 {cluster_name} (類似度: {avg_similarity})")
                lines.append("")
                lines.append(
                    f"**所属ラウンド**: {', '.join([f'Round {r}' for r in sorted(rounds)])}"
                )
                lines.append("")

                # Create table
                lines.append("| ラウンド | 攻撃配置画像 | 防衛配置画像 | メモ |")
                lines.append("|---------|------------|------------|------|")

                for round_num in sorted(rounds):
                    if round_num not in positions_data:
                        continue

                    pos = positions_data[round_num]
                    minimap_file = pos.minimap_file
                    attack_count = len(pos.attack)
                    defend_count = len(pos.defend)

                    lines.append(
                        f"| Round {round_num} "
                        f"(![{minimap_file}]({minimap_file})) "
                        f"|  "
                        f"|  |"
                    )

                lines.append("")
                lines.append("")

        # Detailed round information
        lines.append("---")
        lines.append("")
        lines.append("## ラウンド別詳細")
        lines.append("")

        for round_num in sorted(positions_data.keys()):
            pos = positions_data[round_num]

            lines.append(f"### Round {round_num} (1:40)")
            lines.append("")
            lines.append(f"**タイムスタンプ**: {pos.timestamp:.2f}s")
            lines.append("")

            # Attack team
            lines.append("**攻撃側**:")
            for agent in pos.attack:
                lines.append(
                    f"- {agent['agent']} ({agent['x']:.2f}, {agent['y']:.2f}) - 信頼度: {agent['confidence']:.2%}"
                )

            lines.append("")

            # Defend team
            lines.append("**防衛側**:")
            for agent in pos.defend:
                lines.append(
                    f"- {agent['agent']} ({agent['x']:.2f}, {agent['y']:.2f}) - 信頼度: {agent['confidence']:.2%}"
                )

            lines.append("")
            lines.append(f"![Minimap]({pos.minimap_file})")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Add notes section for manual editing
        lines.append("")
        lines.append("## メモ")
        lines.append("")
        lines.append("※ 手動で追加してください")
        lines.append("")

        markdown_content = "\n".join(lines)

        return markdown_content

    def save_report(self, markdown_content: str, filename: str = "scouting_report.md"):
        """
        Save markdown report to file
        """
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.info(f"Saved scouting report to: {filepath}")

        return filepath

    def generate_html_report(
        self, markdown_content: str, filename: str = "scouting_report.html"
    ):
        """
        Generate HTML report from markdown
        """
        try:
            import markdown
        except ImportError:
            logger.warning("markdown library not found, saving as markdown only")
            return self.save_report(markdown_content, filename.replace(".html", ".md"))

        # Convert markdown to HTML
        html_content = markdown.markdown(
            markdown_content, extensions=["tables", "fenced_code"]
        )

        # Wrap in HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スカウティングレポート</title>
    <style>
        body {{
            font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2, h3 {{
            color: #333;
            border-bottom: 2px solid #00a65a;
            padding-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            background-color: white;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            background-color: #00a65a;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        img {{
            max-width: 300px;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .cluster {{
            background-color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>
"""

        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_template)

        logger.info(f"Saved HTML report to: {filepath}")

        return filepath
