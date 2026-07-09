import time

class FlowCounter:
    def __init__(self, line_y=240):
        self.line_y = line_y

        # IN / OUT
        self.in_count = 0
        self.out_count = 0
        self.counted_ids = set()

        # ✅ 必须初始化（你现在报错的根源）
        self.history = {}

    def update(self, track_id, cy):
        if track_id == -1:
            return

        # ======================
        # 轨迹记录
        # ======================
        if track_id in self.history:
            last_y = self.history[track_id]

            # 向下穿过线 → IN
            if last_y < self.line_y <= cy:
                if track_id not in self.counted_ids:
                    self.in_count += 1
                    self.counted_ids.add(track_id)

            # 向上穿过线 → OUT
            elif last_y > self.line_y >= cy:
                if track_id not in self.counted_ids:
                    self.out_count += 1
                    self.counted_ids.add(track_id)

        # 更新历史位置
        self.history[track_id] = cy

    def get_stats(self):
        return {
            "in_count": self.in_count,
            "out_count": self.out_count
        }