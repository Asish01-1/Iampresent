from datetime import datetime


class AttendanceManager:

    def __init__(self):
        self.present_today = set()

    def mark_present(self, student_id, confidence):

        if student_id in self.present_today:
            return False

        self.present_today.add(student_id)

        print(
            f"Attendance marked: {student_id} "
            f"confidence={confidence:.3f}"
        )

        return True