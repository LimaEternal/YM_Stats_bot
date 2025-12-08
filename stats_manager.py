import json
from datetime import datetime, timedelta
import os


class MusicStats:
    """Класс для хранения статистики за один день"""

    def __init__(self, date, total_seconds, total_tracks):
        self.date = date  # Формат: YYYY-MM-DD
        self.total_seconds = total_seconds
        self.total_tracks = total_tracks

    def to_dict(self):
        return {
            "date": self.date,
            "total_seconds": self.total_seconds,
            "total_tracks": self.total_tracks,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data["date"], data["total_seconds"], data["total_tracks"])

    def __str__(self):
        hours = self.total_seconds / 3600
        return f"{self.date}: {self.total_seconds//60} мин ({hours:.2f} ч), треков: {self.total_tracks}"


class StatsStorage:
    """Класс для сохранения и загрузки статистики в текстовый файл"""

    def __init__(self, filename="music_stats.json"):
        self.filename = filename

    def load_all_stats(self):
        """Загружает всю статистику из файла"""
        try:
            if not os.path.exists(self.filename):
                return []

            with open(self.filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [MusicStats.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def save_stats(self, stats):
        """Сохраняет статистику в файл"""
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(
                [stat.to_dict() for stat in stats], f, indent=2, ensure_ascii=False
            )

    def has_data_for_date(self, date):
        """Проверяет, есть ли уже данные за указанную дату"""
        all_stats = self.load_all_stats()
        return any(stat.date == date for stat in all_stats)

    def get_latest_stats(self):
        """Получает последнюю сохраненную статистику"""
        all_stats = self.load_all_stats()
        if not all_stats:
            return None
        return max(all_stats, key=lambda x: x.date)

    def calculate_daily_diff(self, current_stats, previous_stats):
        """Вычисляет дневную разницу между двумя записями"""
        if not previous_stats:
            return current_stats.total_seconds, current_stats.total_tracks

        # Проверяем на сброс счетчиков (начало нового месяца)
        if current_stats.total_seconds < previous_stats.total_seconds:
            return current_stats.total_seconds, current_stats.total_tracks

        # Вычисляем разницу
        seconds_diff = current_stats.total_seconds - previous_stats.total_seconds
        tracks_diff = current_stats.total_tracks - previous_stats.total_tracks

        # Защита от отрицательных значений
        return max(0, seconds_diff), max(0, tracks_diff)

    def get_monthly_stats(self, year, month):
        """Получает общую статистику за месяц (последние доступные данные)"""
        all_stats = self.load_all_stats()
        if not all_stats:
            return None

        # Фильтруем записи за указанный месяц
        month_prefix = f"{year}-{month:02d}-"
        month_stats = [stat for stat in all_stats if stat.date.startswith(month_prefix)]

        if not month_stats:
            return None

        # Берем самую последнюю запись за месяц
        return max(month_stats, key=lambda x: x.date)

    def get_last_two_days_stats(self):
        """Получает статистику за последние два дня для сравнения"""
        all_stats = self.load_all_stats()
        if len(all_stats) < 2:
            return None, None

        # Сортируем по дате по убыванию
        sorted_stats = sorted(all_stats, key=lambda x: x.date, reverse=True)
        return sorted_stats[0], sorted_stats[1]
